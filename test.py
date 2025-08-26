link = 'https://www.kbb.com/toyota/prius/2006/hatchback-4d/options/?category=hatchback&intent=buy-used&mileage=0&pricetype=private-party&vehicleid=1595'


def test():
    new_params = '?condition=good&intent=buy-used&mileage=0&pricetype=private-party'
    # Split the link at 'options/' and take the first part, which is the base URL you want.
    base_url = link.split('options/')[0]
    # Combine the base URL with your new parameters.
    new_link = base_url + new_params
    print("ns: " + new_link)

test()