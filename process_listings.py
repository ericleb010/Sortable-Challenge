from setup_json import mfrs, listings, final_obj
import re
import json

result = {}
bad_keywords = re.compile("f[o|ü]r|pour") # Pre-compiling regex object for eradicating accessory listings


# For conversion into USD.
def convert_currency(curr, val):
    if curr == 'USD':
        return val
    if curr == 'EUR':
        return val * 1.05
    if curr == 'GBP':
        return val * 1.25
    if curr == 'CAD':
        return val * 0.75


# This is the main part of the program, which attempts to match
# a listing to one of the products we've already categorized.
# It also helps generate the average price for a model.
def make_listings():
    for listing_obj in listings:
        # Listing preprocessing. "With" usually indicates when the listing stopped being useful.
        listing_init = listing_obj["title"].lower()
        listing = listing_init.split("with")[0].split("w/")[0].split("mit")[0].split("avec")[0].replace(",", "")

        # Ignore all accessories.
        if re.search(bad_keywords, listing):
            continue

        # Shorter names
        listing_mfr = listing_obj["manufacturer"].lower()
        price = convert_currency(listing_obj["currency"], float(listing_obj["price"]))

        found = False
        for mfr in mfrs.keys():
            if found: break
            # Check if the manufacturer had two parts...
            for mfr_word in mfr.split(" "):
                if found: break
                # ...search listing and manufacturer field for either word independently.
                if listing_mfr.find(mfr_word) is not -1 or listing.find(mfr_word) is not -1:
                    unclassified = mfrs[mfr]["families"].get("unclassified", None)
                    for family in mfrs[mfr]["families"].keys():
                        if found: break
                        family_obj = mfrs[mfr]["families"][family]
                        match = None
                        # Check the model against the listing.
                        for model in family_obj["models"].keys():
                            model_obj = family_obj["models"][model]
                            pattern = model_obj["pattern"] # Precompiled regex object from setup_json
                            spaces = model.split(" ") # Do we have spaces / dashes?

                            match_candidate = re.search(pattern, listing)
                            if match_candidate and (
                                     match is None or
                                     len(match_candidate.group(1)) > len(match.group(1))):

                                # Here, we've found the largest match thus far for this listing.
                                match = match_candidate
                                matched_model = model
                                found = True

                            # If we didn't match, but we have multiple words to process,
                            # try to locate all of them.
                            elif len(spaces) > 1:
                                for term in spaces:
                                    if not re.search(term, listing):
                                        break # We need to match every term for success.
                                else:
                                    # Didn't break out. Check if it's the largest match.
                                    curr_model = model.replace(" ", "")
                                    if match is None or len(curr_model) > len(match.group(1)):
                                        match = re.search("(" + curr_model + ")", curr_model)
                                        matched_model = model
                                        found = True

                        if found or (unclassified and family in unclassified.keys()):
                            # If we matched the model number:
                            if found:
                                model_obj = family_obj["models"][matched_model]
                            else:
                                family_obj = unclassified
                                model_obj = family_obj["models"]

                            # Aggregate the stats we found.
                            model_obj["agg_price"] += price
                            model_obj["count"] += 1
                            # Stuff listing into product list.
                            final_obj[model_obj["name"]].append(listing_obj)


# This function either removes false-positive listings from averages
# or erases false-positive listings from the results array, based on the price.
# avg_inflation_frac is a fraction for very high priced listings (usually that's OK)
# listing_under_factor is a constant for very low priced listings
# remove -- True: wipes from results; False: wipes from averages
def truncate_bad_prices(avg_inflation_frac, listing_under_factor, remove):
    for mfr in mfrs:
        for family in mfrs[mfr]["families"]:
            model_obj = mfrs[mfr]["families"][family]["models"]
            for model in model_obj:
                for listing in final_obj[model_obj[model]["name"]]:
                    avg_price = (model_obj[model]["agg_price"] / model_obj[model]["count"])
                    price_diff = avg_price / float(listing["price"])
                    if price_diff < avg_inflation_frac or price_diff > listing_under_factor:
                        if remove:
                            final_obj[model_obj[model]["name"]].remove(listing)
                            return
                        model_obj[model]["agg_price"] -= convert_currency(listing["currency"], float(listing["price"]))
                        model_obj[model]["count"] -= 1


# Outputs everything when finished.
def output_to_file():
    f = open("results.txt", "w")
    for product in final_obj:
        f.write(json.dumps({"product_name": product, "listings": final_obj[product]}) + "\n")
    f.close()


if __name__ == "__main__":
    make_listings()
    truncate_bad_prices(0.3, 4, False)
    truncate_bad_prices(0.1, 3, True)
    output_to_file()