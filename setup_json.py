import json
import re


mfrs = {}       # Products list: manufacturer -> product family -> model
final_obj = {}  # Final object that will eventually hold all product listings.


# This is meant to set up the data structure which categorizes known products.
for product_json in open("products.txt").read().split('\n')[:-1]:
    p = json.loads(product_json)

    # Preprocessing product text
    mfr = p["manufacturer"].strip().lower()
    family = p.get("family", "unclassified").strip().lower().replace("-", " ").replace("!", "")
    model = p["model"].strip().lower().replace("-", " ")

    # An awful lot of Sony listings do not include "DSLR" even though it's in the model number...
    # Should be save to ignore that part of the model, since no camera should ever be called "DSLR"!
    spaced = model.split(" ")
    if len(spaced) > 1:
        for i in range(0, len(spaced)):
            if spaced[i].find("dslr") is not -1:
                model = re.sub("\s?" + "dslr" + ("\s?" if i is 0 else ""), "", model)
                break

    # Structure initialization
    if mfr not in mfrs:
        mfrs[mfr] = {"families": {}}
    if family not in mfrs[mfr]["families"]:
        mfrs[mfr]["families"][family] = {"models": {}}
    mfrs[mfr]["families"][family]["models"][model] = {
        "agg_price": 0,
        "count": 0,
        "pattern": re.compile("[\s|dslr|\-](" + model + ")[a-z]*\s"),
        "name": p["product_name"],
        "date": p["announced-date"]
    }

    # Initialize room for the result object for this product.
    final_obj[p["product_name"]] = []


# While we're at it, might as well load the listings too.
listings = list(map(lambda x: json.loads(x), open("listings.txt").read().split('\n')[:-1]))
