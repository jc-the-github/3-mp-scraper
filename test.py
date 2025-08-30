link = 'https://www.kbb.com/toyota/prius/2006/hatchback-4d/options/?category=hatchback&intent=buy-used&mileage=0&pricetype=private-party&vehicleid=1595'

list: 2015 Nissan murano Platinum Sport Utility 4D
list: 2003 Lincoln navigator
list: 2024 Endurance endurance
list: 2002 Lexus rx 300
list: 1964 Volkswagen beetle 1.8T Classic Hatchback 2D
list: 2015 Nissan altima 2.5 SV Sedan 4D
list: 2014 Mercedes-Benz e63 amg 4matic s-model
list: 2000 Ford expedition Eddie Bauer Sport Utility 4D
list: Seadoo Jetski trailer

list: 2013 Kia rio
list: 2014 Toyota camry SE Sport Sedan 4D
list: 2003 Nissan maxima S Sedan 4D
list: 2002 Lexus ES 300 Sedan 4D
list: 2007 Nissan murano
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1756519916.381556  115524 voice_transcription.cc:58] Registering VoiceTranscriptionCapability
list: 2011 Honda cr-v LX Sport Utility 4D
list: 2015 Jeep cherokee Latitude Sport Utility 4D
def test():
    new_params = '?condition=good&intent=buy-used&mileage=0&pricetype=private-party'
    # Split the link at 'options/' and take the first part, which is the base URL you want.
    base_url = link.split('options/')[0]
    # Combine the base URL with your new parameters.
    new_link = base_url + new_params
    print("ns: " + new_link)

test()