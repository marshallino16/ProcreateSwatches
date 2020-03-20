import requests
import re
from selenium import webdriver
from colour import Color
from slugify import slugify
import zipfile
import json


def divide_chunks(list_elements, max_nb_elements):
    for i in range(0, len(list_elements), max_nb_elements):
        yield list_elements[i:i + max_nb_elements]


class ColorHuntSwatches:

    def __init__(self):
        self.regex = r".*?\"id\":\"([^\"]*)\".*?"
        self.regex_hex = r".*?\">(#[\S]*)<\/.*?"
        self.colors = []
        self.name = "ColorHunt"
        self.limit_max_colors = 30
        self.number_page_to_scrape = 3

    def get_palettes(self):

        # Iterate over pages
        for step in range(self.number_page_to_scrape):
            url = 'https://colorhunt.co/hunt.php'
            params = {'step': '%d' % step, 'sort': 'popular', 'tags': ''}

            palettes = requests.post(url, data=params)

            matches = re.findall(self.regex, palettes.text)
            # print(matches)

            for match in matches:
                self.get_colors(match)

        # Divide colors list into chunks
        chunks = list(divide_chunks(self.colors, self.limit_max_colors))
        for i in range(len(chunks)):
            chunk = chunks[i]

            zf = zipfile.ZipFile(slugify(self.name + str(i)) + '.swatches', mode='w')

            json_obj = []
            json_obj.append({"name": self.name + '#' + str(i), "swatches": chunk})
            json_string = json.dumps(json_obj)

            zf.writestr('Swatches.json', json_string)
            zf.close()

            print("...created " + slugify(self.name + str(i)) + ".swatches")

    def get_colors(self, palette_id):
        url = "https://colorhunt.co/palette/%s" % palette_id

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        driver = webdriver.Chrome(executable_path='./chromedriver', options=options)
        driver.get(url)

        current_palette = driver.find_element_by_xpath('//*[@id="feed"]/div[1]/div[1]')
        palette_elements = current_palette.find_elements_by_class_name('place')

        hex_colors = []
        for palette_element in palette_elements:
            background_colors = re.findall(self.regex_hex, palette_element.get_attribute('innerHTML'))
            if len(background_colors) > 0:
                hex_colors.append(background_colors[0])

        self.convert_hex_to_hsl(hex_colors)

    def convert_hex_to_hsl(self, hex_colors):
        for color in hex_colors:
            c = Color(color)
            c_obj = {"hue": c.hue, "brightness": c.luminance, "saturation": c.saturation, "alpha": 1, "colorspace": 0}
            if c_obj not in self.colors:
                self.colors.append(c_obj)


if __name__ == '__main__':
    colorHuntSwatches = ColorHuntSwatches()
    colorHuntSwatches.get_palettes()
