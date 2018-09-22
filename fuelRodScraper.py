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

dpfrl_server_url = "insert_webserver_here"

#The first xpath gets each section
first_xpath = "//div[@class='nodeContainer']"
#The second xpath gets the section title
second_xpath = "./div/div[@class='title']/text()"
#The third xpath gets the kiosks
third_xpath = ".//div[@class='textContainer']/div/text()"
#And the fourth gets the coords
fourth_xpath = ".//div[@class='node child']/@data-id"

def match_description(label):
    descriptions = json.loads(open("descriptions.json").read())
    if(label in descriptions):
        return descriptions[label]
    else:
        return "Ask a Cast Member for the location of this Kiosk"

def scrape(url, label):
    browser = ""

    def wait_for(condition_fn, error_message, timeout_seconds):
        print("Waiting for page to initalize..")
        start = time.time()
        time_count = 0
        while time.time() - start < timeout_seconds:
            if condition_fn():
                print("Webpage has initiated, took %d seconds" % time_count)
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
            print("Connecting to %s" % url)
            browser.get(url)
            print("Connected to webpage")
            wait_for(is_data_loaded, "Page didn't load", 60)
            innerHTML = browser.execute_script("return document.body.innerHTML")
            htmlString = innerHTML
        except common.exceptions.WebDriverException as e:
            print(bcolor.FAIL + "Webdriver Error: " + e.msg + bcolor.ENDC)
            sys.exit("Webdriver Error")
        except common.exceptions.AssertionError:
            sys.exit("Webpage didn't load")
        except:
            print("Unexpected error: ", sys.exc_info()[0])
            print(bcolor.FAIL + "Website didn't load in time" + bcolor.ENDC)
            sys.exit("Website Error")
        finally:
            browser.quit()

        tree = html.fromstring(htmlString)
        section = tree.xpath(first_xpath)
        fancy_listy = []
        for park in section:
            tag = park.xpath(second_xpath)[0]
            name_entries = park.xpath(third_xpath)
            formatted_names =[]
            for name in name_entries:
                split_name = name.split()[6:]
                split_name[0] = split_name[0].capitalize()
                formatted_names.append(" ".join(split_name))
            
            coord_entries = park.xpath(fourth_xpath)
            formatted_coords = []
            for coord in coord_entries:
                pair = coord.split(";")[2:]
                formatted_coords.append(pair)
            
            for i in range(len(formatted_names)):
                kiosk = {
                    'location': formatted_names[i],
                    'coords': formatted_coords[i],
                    'desc': match_description(formatted_names[i]),
                    'tag': tag
                }
                fancy_listy.append(kiosk)
        
        final_formatted = {
            'resort': label,
            'kiosks': fancy_listy
        }
        return final_formatted

def send(data):
    label = data['label']
    print("Preparing to send")
    # Dumping for posterity
    with open(label + '.json', 'w') as fp:
        json.dump(data, fp)
        print((bcolors.OKGREEN + "%s saved to %s.json" + bcolors.ENDC) % (label, label))
    #Generating signature using PyCrypto
    string_data = json.dumps(data)
    signature = signer.sign_data("private_key.txt", b64encode(string_data.encode('ascii')))
    payload = {
        "signature": signature,
        "payload": string_data
    }
    r = requests.post(dpfrl_server_url, data=payload)
    print("Posting returned a %d status, with the JSON of %s" % (r.status_code, r.text))

all_builder = {
    "label": "all_resorts",
    "lists": []
}

for resort in resorts:
    print(bcolors.HEADER + "FuelRodScraper scraping %s" % (resort['label']) + bcolors.ENDC)
    all_builder["lists"].append(scrape(resort['url'], resort['label']))

send(all_builder)
print(bcolors.OKGREEN + "Scraping Complete. Have a magical day." + bcolors.ENDC)