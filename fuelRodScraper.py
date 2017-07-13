#!/usr/bin/python2.7
from pyvirtualdisplay import Display
from selenium import webdriver, common
from lxml import html
from base64 import b64encode
import sys
import time
import json
import signer
import requests

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

resorts = [
    {
        "label": "disneyworld",
        "url": "http://disneyworld.disney.go.com/maps/service-details/18579731%3bentitytype%3dguest-service"
    },
    {
        "label": "disneyland",
        "url": "http://disneyland.disney.go.com/maps/service-details/18583410%3bentitytype%3dguest-service"
    }
]

dpfrl_server_url = "http://thomasstoeckert.pythonanywhere.com/fuelrod_post/"

names_xpath = "//div[@class='textContainer']/div/text()"
coords_xpath = "//div[@class='textContainer']/parent::div/@data-id"

def match_description(label):
    descriptions = json.loads(open("descriptions.json").read())
    if(label in descriptions):
        return descriptions[label]
    else:
        return "Ask a Cast Member for the location of this Kiosk"

def scrape(url, label):
    browser = ""

    def wait_for(condition_fn, error_message, timeout_seconds):
        print "Waiting for page to initalize..."
        start = time.time()
        time_count = 0
        while time.time() - start < timeout_seconds:
            if condition_fn():
                print "Webpage has initiated, took %d seconds" % time_count
                return
            time_count += 1
            time.sleep(1)
        raise AssertionError(error_message)

    def is_data_loaded():
        try:
            browser_check = browser.find_element_by_class_name('name')
            return True
        except common.exceptions.NoSuchElementException:
            return False
        except:
            return False

    htmlString = ""
    with Display():
        browser = webdriver.Firefox(executable_path=r'./geckodriver')
        try:
            print "Connecting to %s" % url
            browser.get(url)
            print "Connected to webpage"
            wait_for(is_data_loaded, "Page didn't load", 60)
            innerHTML = browser.execute_script("return document.body.innerHTML")
            htmlString = innerHTML
        except common.exceptions.WebDriverException as e:
            print bcolor.FAIL + "Webdriver Error: " + e.msg + bcolor.ENDC
            sys.exit("Webdriver Error")
        except common.exceptions.AssertionError:
            sys.exit("Webpage didn't load")
        except:
            print "Unexpected error: ", sys.exc_info()[0]
            print bcolor.FAIL + "Website didn't load in time" + bcolor.ENDC
            sys.exit("Website Error")
        finally:
            browser.quit()

        tree = html.fromstring(htmlString)
        names_raw = tree.xpath(names_xpath)
        coords_raw = tree.xpath(coords_xpath)

        # Format Names
        names_formatted = []
        for name in names_raw:
            # This is the trimmed, split name of the kiosk
            split_name = name.split()[6:]
            # Then we capitalize the first item in the name
            split_name[0] = split_name[0].capitalize()
            names_formatted.append(" ".join(split_name))
        
        # Format Coords
        coords_formatted = []
        for coord in coords_raw:
            pair = coord.split(";")[2:]
            coords_formatted.append(pair)
        
        list_formatted = []
        for i in range(len(names_formatted)):
            entry = {
                'location': names_formatted[i],
                'coords': coords_formatted[i],
                'desc': match_description(names_formatted[i])
            }
            list_formatted.append(entry)
        
        final_formatted = {
            'resort': label,
            'kiosks': list_formatted
        }
        return final_formatted

def send(data):
    label = data['label']
    print "Preparing to send"
    # Dumping for posterity
    with open(label + '.json', 'w') as fp:
        json.dump(data, fp)
        print (bcolors.OKGREEN + "%s saved to %s.json" + bcolors.ENDC) % (label, label)
    #Generating signature using PyCrypto
    string_data = json.dumps(data)
    signature = signer.sign_data("private_key.txt", b64encode(string_data))
    payload = {
        "signature": signature,
        "payload": string_data
    }
    r = requests.post(dpfrl_server_url, data=payload)
    print "Posting returned a %d status, with the JSON of %s" % (r.status_code, r.text)

all_builder = {
    "label": "all_resorts",
    "lists": []
}

for resort in resorts:
    print bcolors.HEADER + "FuelRodScraper scraping %s" % (resort['label']) + bcolors.ENDC
    all_builder["lists"].append(scrape(resort['url'], resort['label']))

send(all_builder)
print bcolors.OKGREEN + "Scraping Complete. Have a magical day." + bcolors.ENDC