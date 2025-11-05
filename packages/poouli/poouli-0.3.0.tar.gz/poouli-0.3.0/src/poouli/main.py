import os
import re
from pathlib import Path
from typing import List, Optional
import pywikibot as pwb
import pypandoc as pdc
import yaml
import frontmatter as fm
from datetime import datetime, timezone

from poouli.load_config import load_config

def print_snippet(cfg, note_metadata):
	if type(note_metadata.get('wiki_styling')) is str:
		styling = note_metadata['wiki_styling']
	else:
		styling = cfg.get('styling')
	if type(note_metadata.get('wiki_banner')) is str:
		banner = note_metadata['wiki_banner']
	else:
		banner = cfg.get('banner')
	if note_metadata.get('wiki_styling') and styling and banner:
		snippet = '<!-- START AUTO-GENERATED SNIPPET -->\n<noinclude>\n\n<!-- Page styling -->\n' + styling + '\n\n<! -- Cross-posting disclaimer banner -->\n' + banner + '\n</noinclude>\n<!-- END AUTO-GENERATED SNIPPET -->'
	elif note_metadata.get('wiki_styling') and styling:
		snippet = '<!-- START AUTO-GENERATED SNIPPET -->\n<noinclude>\n\n<!-- Page styling -->\n' + styling + '\n</noinclude>\n<!-- END AUTO-GENERATED SNIPPET -->'
	elif cfg.get('banner'): # +++ and note_metadata.get('wiki_banner') != False:
		snippet = '<!-- START AUTO-GENERATED SNIPPET -->\n<noinclude>\n' + '\n\n<!-- Cross-posting disclaimer banner -->\n' + banner + '\n</noinclude>\n<!-- END AUTO-GENERATED SNIPPET -->'
	else:
		snippet = ''
	return snippet

def sync_wiki(cfg):
	site = pwb.Site('en', 'pzwiki')
	local_directory = Path(cfg['local_directory']).expanduser()
	print(f'Local folder: {local_directory}')
	print(type(os.listdir(local_directory)))
	print(os.listdir(local_directory))
	for note in os.listdir(local_directory):
		note_path = os.path.join(local_directory, note)
		note_metadata = fm.load(note_path).metadata
		print(f'Processing {note_path}')
		if note_metadata.get('wiki_exclude') != True:
			if 'wiki_title' in note_metadata:
				wiki_title = note_metadata.get('wiki_title')
			elif 'title' in note_metadata:
				wiki_title = f'{cfg['wiki_base_path']}/{note_metadata.get('title')}'
			else:
				wiki_title = f'{cfg['wiki_base_path']}/{Path(note_path).stem}'
			page = pwb.Page(site, str(wiki_title))
			if page.exists():
				wiki_updated = page.latest_revision.timestamp.replace(tzinfo=timezone.utc)
				print(f'Latest revision on wiki: {wiki_updated}')
				print(f'Type of wiki_updated: {type(wiki_updated)}')
				print(f'Type of note_metadata[\'updated\']: {type(note_metadata['updated'])}')
			else:
				wiki_updated = None
				print(f'Page “{wiki_title}” does not exist, creating it…')
			# if there are no source files specified in the config file, the snippet preferences are not loaded anyways
			snippet = print_snippet(cfg, note_metadata)
			if 'updated' in note_metadata and wiki_updated != None:
				if isinstance(note_metadata['updated'], str):
					note_metadata['updated'] = datetime.fromisoformat(note_metadata['updated'])
				if wiki_updated > note_metadata['updated']:
					pull = input(f'It looks like there is a newer version of {wiki_title} on the Wiki. Do you want to pull it [y/n]? ').lower()
					if 'y' in pull:
						pull_wiki(page, note_path, wiki_updated)
				else:
					push_wiki(page, wiki_title, note_path, snippet)
			else:
				push = input(f'The local file for {wiki_title} has no updated date. Do you want to push it [y/n]? ').lower()
				if 'y' in push:
					push_wiki(page, wiki_title, note_path, snippet)
		else:
			print(f'`wiki_exclude` is True for {note_path}')

def pull_wiki(page, note_path, updated):
	print(f'The Wiki page has more recent changes.')
	note = fm.load(note_path)
	note.metadata['updated'] = updated.isoformat()
	content = re.sub(r'(?s)<!-- START AUTO-GENERATED SNIPPET -->.*?<!-- END AUTO-GENERATED SNIPPET -->', '', page.text)
	note.content = pdc.convert_text(content, format='mediawiki', to='commonmark', extra_args=['--wrap=none'])
	note = fm.dumps(note)
	with open(note_path, 'w', encoding='utf-8') as local_note:
		local_note.write(note)
	print(f'Updated local note {note_path}')

def push_wiki(page, title, note_path, snippet):
	print(f'Destination URL: https://pzwiki.wdka.nl/mediadesign/{title}')
	page_content = pdc.convert_file(note_path, 'mediawiki', extra_args=['--wrap=none'])
	page_content += snippet
	page.text = page_content
	page.save(summary='Updated via Pöuli')

cfg = load_config()
sync_wiki(cfg)
