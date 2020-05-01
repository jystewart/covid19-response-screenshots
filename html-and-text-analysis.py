import textstat
import trafilatura
import requests
import dragnet
from lxml import html
import json
from datetime import datetime
import os
import errno
import re

formatted_date = datetime.now().strftime("%Y-%m-%d")
output_directory = "/home/james/screenshots"
html_output_directory = os.path.join(output_directory, formatted_date)
json_output_directory= os.path.join(output_directory, "language-analysis")

output_for_json = {}

# Ensure output folders exist
try:
    os.makedirs(html_output_directory)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise
try:
    os.makedirs(json_output_directory)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

def process_trafilatura(downloaded):
  downloaded = html.fromstring(downloaded)
  return trafilatura.extract(downloaded)

def process_dragnet(downloaded):
  return dragnet.extract_content(downloaded)

def get_scores(text):
  scores = {}
  try:
    scores['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
    scores['smog'] = textstat.smog_index(text)
    scores['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
    scores['coleman_liau'] = textstat.coleman_liau_index(text)
    scores['automated_readability'] = textstat.automated_readability_index(text)
    scores['dale_chall_readability'] = textstat.dale_chall_readability_score(text)
    scores['difficult_words'] = textstat.difficult_words(text)
    scores['linsear_write_formula'] = textstat.linsear_write_formula(text)
    scores['gunning_fog'] = textstat.gunning_fog(text)
    scores['standard'] = textstat.text_standard(text)
    return scores
  except Exception as e:
      return repr(e)

def filter_bad_filename_chars(filename):
    """
        Filter bad chars for any filename
    """
    # Before, just avoid triple underscore escape for the classic '://' pattern
    filename = filename.replace('://', '_')

    return re.sub('[^\w\-_\. ]', '_', filename)

markdown_file = open(os.path.join(output_directory, "language-analysis.md"), "w")

markdown_file.write(" | URL | Trafilatura | Dragnet |\n")
markdown_file.write(" | --- | --- | --- |\n")

fl = open(os.path.join(output_directory, 'list.txt'))
for raw_url in fl:
  url = raw_url.strip()
  output_for_json[url] = {'dragnet' : {}, 'trafilatura': {}}

  try:
    downloaded = requests.get(url).text
  except Exception as e:
    traf_msg = repr(e)
    markdown_file.write(f" | {url} | {traf_msg} | |")
    output_for_json[url]['error'] = traf_msg
    continue

  # First thing we do is capture the HTML
  try:
    output_filename = os.path.join(html_output_directory, ('%s.html' % filter_bad_filename_chars(url)))
    html_file = open(output_filename, "w")
    html_file.write(downloaded)
    html_file.close()
  except:
    # For now we don't worry if it doesn't save, we just let the user know
    print(f"Failed to store HTML for {url}")

  try:
    traf_text = process_trafilatura(downloaded)
    output_for_json[url]['trafilatura'] = get_scores(traf_text)
    traf_msg = output_for_json[url]['trafilatura']['standard']
  except Exception as e:
      output_for_json[url]['trafilatura'] = {'error' : repr(e)}

  try:
    dragnet_text = process_dragnet(downloaded)
    output_for_json[url]['dragnet'] = get_scores(dragnet_text)
    dragnet_msg = output_for_json[url]['dragnet']['standard']
  except Exception as e:
    output_for_json[url]['dragnet'] = {'error' : repr(e)}

  markdown_file.write(f" | {url} | {traf_msg} | {dragnet_msg} |")
  markdown_file.write("\n")

fl.close()
markdown_file.close()

json_filename = os.path.join(json_output_directory, ('%s.json' % formatted_date))
json_file = open(json_filename, "w")
json_file.write(json.dumps(output_for_json, indent=2, sort_keys=True))
json_file.close()

