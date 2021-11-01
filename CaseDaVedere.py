#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# This file is part of the emisilve86 distribution (https://github.com/emisilve86).
# Copyright (c) 2021 Emiliano Silvestri.
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import os
import re
import json
import socket
import validators
import http.client
import base64

from datetime import datetime
from bs4 import BeautifulSoup
from email.mime.text import MIMEText


##########################################
# PARAMETRI PER LA CONNESSIONE AL SERVER #
##########################################

casedavedere_host = 'www.casedavedere.it'
casedavedere_url = 'https://www.casedavedere.it/vendita-case/{0}/pag={1}'


################################################
# HTML CONTENENTE GLI ULTIMI IMMOBILI FILTRATI #
################################################

filtered_property = 'casedavedere.html'


############################################################
# TESTO CONTENENTE I CODICI DEGLI ULTIMI IMMOBILI FILTRATI #
############################################################

property_code = 'property_code.txt'


####################################################
# IMMOBILI FILTRATI PER CARATTERISTICHE DESIDERATE #
####################################################

property_dict = {}
property_list = []
new_property_list = []


#################################
# CARATTERISTICHE DELL'IMMOBILE #
#################################

class Property:
	
	def __init__(self, link, html):
		self.__link = link
		self.__html = html
		self.__code = None
		self.__area = None
		self.__price = None
		self.__floor = None
		self.__max_floor = None
		self.__rooms = None
		self.__balcony = None
		self.__box = None
		self.__elevator = None
	
	def get_link(self):
		return self.__link
	
	def get_html(self):
		return self.__html
	
	def get_code(self):
		return self.__code
	
	def set_code(self, code):
		if re.fullmatch('[0-9]+-[0-9]+', code):
			self.__code = code
	
	def get_area(self):
		return self.__area
	
	def set_area(self, area):
		if area.isnumeric():
			self.__area = int(area)
	
	def get_price(self):
		return self.__price
	
	def set_price(self, price):
		if price.isnumeric():
			self.__price = int(price)
	
	def get_floor(self):
		return self.__floor
	
	def set_floor(self, floor):
		if '>' in floor:
			floor = floor.strip('>')
		if floor.isnumeric():
			self.__floor = int(floor)
	
	def get_max_floor(self):
		return self.__max_floor
	
	def set_max_floor(self, max_floor):
		if max_floor.isnumeric():
			self.__max_floor = int(max_floor)
	
	def get_rooms(self):
		return self.__rooms
	
	def set_rooms(self, rooms):
		if rooms.isnumeric():
			self.__rooms = int(rooms)
	
	def get_balcony(self):
		return self.__balcony
	
	def set_balcony(self, balcony):
		if balcony.isnumeric():
			self.__balcony = int(balcony)
		elif 'no' in balcony.lower() or 'assente' in balcony.lower():
			self.__balcony = 0
		elif 'si' in balcony.lower() or 'uno' in balcony.lower():
			self.__balcony = 1
		elif 'due' in balcony.lower():
			self.__balcony = 2
		elif 'tre' in balcony.lower():
			self.__balcony = 3
	
	def get_box(self):
		return self.__box
	
	def set_box(self, box):
		if 'si' in box.lower():
			self.__box = True
		elif 'no' in box.lower() or 'assente' in box.lower():
			self.__box = False
	
	def get_elevator(self):
		return self.__elevator
	
	def set_elevator(self, elevator):
		if 'si' in elevator.lower():
			self.__elevator = True
		elif 'no' in elevator.lower() or 'assente' in elevator.lower():
			self.__elevator = False


############################################
# CARATTERISTICHE DELL'IMMOBILE DESIDERATE #
############################################

class PropertyFilter:
	
	def __init__(self, min_area=0, max_area=10**3, min_price=0,
				  max_price=10**6, int_floor=False, min_rooms=0,
				    min_balconies=0, box=False, elevator=False):
		self.__min_area = min_area
		self.__max_area = max_area
		self.__min_price = min_price
		self.__max_price = max_price
		self.__intermediate_floor = int_floor
		self.__min_rooms = min_rooms
		self.__min_balconies = min_balconies
		self.__need_box = box
		self.__need_elevator = elevator
	
	def __filter_area(self, area):
		if area is None:
			return True
		return self.__min_area <= area <= self.__max_area
	
	def __filter_price(self, price):
		if price is None:
			return True
		return self.__min_price <= price <= self.__max_price
	
	def __filter_floor(self, floor, max_floor):
		if not self.__intermediate_floor:
			return True
		if floor is None or max_floor is None:
			return True
		return floor < max_floor
	
	def __filter_rooms(self, rooms):
		if rooms is None:
			return True
		return rooms >= self.__min_rooms
	
	def __filter_balcony(self, balcony):
		if balcony is None:
			return True
		return balcony >= self.__min_balconies
	
	def __filter_box(self, box):
		if not self.__need_box:
			return True
		if box is None:
			return True
		return box

	def __filter_elevator(self, elevator):
		if not self.__need_elevator:
			return True
		if elevator is None:
			return True
		return elevator
	
	def pass_filter(self, property_obj):
		if not property_obj or not isinstance(property_obj, Property):
			return False
		if not self.__filter_area(property_obj.get_area()):
			return False
		if not self.__filter_price(property_obj.get_price()):
			return False
		if not self.__filter_floor(property_obj.get_floor(), property_obj.get_max_floor()):
			return False
		if not self.__filter_rooms(property_obj.get_rooms()):
			return False
		if not self.__filter_balcony(property_obj.get_balcony()):
			return False
		if not self.__filter_box(property_obj.get_box()):
			return False
		if not self.__filter_elevator(property_obj.get_elevator()):
			return False
		return True
	
	def stamp_filter(self):
		stamp = '<table class="filter">\n'
		stamp += ' <tr><th>Filtro Applicato:</th></tr>\n'
		if self.__min_area != 0 or self.__max_area != 10**3:
			stamp += ' <tr><td>Superficie compresi tra {0} e {1} mq</td></tr>\n'.format(self.__min_area, self.__max_area)
		if self.__min_price != 0 or self.__max_price != 10**6:
			stamp += ' <tr><td>Prezzo compreso tra {0} e {1} €</td></tr>\n'.format(self.__min_price, self.__max_price)
		if self.__intermediate_floor:
			stamp += ' <tr><td>Solo Piani Intermedi</td></tr>\n'
		if self.__min_rooms != 0:
			stamp += ' <tr><td>Almeno {0} Locali</td></tr>\n'.format(self.__min_rooms)
		if self.__min_balconies != 0:
			stamp += ' <tr><td>Almeno {0} Balconi</td></tr>\n'.format(self.__min_balconies)
		if self.__need_box:
			stamp += ' <tr><td>Con Garage/Box</td></tr>\n'
		if self.__need_elevator:
			stamp += ' <tr><td>Con Ascensore</td></tr>\n'
		stamp += '</table>\n'
		return stamp


####################
# FUNZIONI DI RETE #
####################

def resolve_hostname(host):
	try:
		socket.gethostbyname(host)
		return True
	except socket.error:
		return False


def get_html(host, url):
	http_conn = http.client.HTTPSConnection(host)
	http_conn.request('GET', url)
	http_resp = http_conn.getresponse()
	html_data = http_resp.read() if http_resp.status == 200 else None
	http_conn.close()
	return str(html_data) if html_data else None


############################
# FUNZIONI DI PARSING HTML #
############################

def parse_imm(imm_href, imm_table, imm_html):
	if imm_html:
		property_obj = Property(imm_href, imm_table)
		soup = BeautifulSoup(imm_html, 'html.parser')
		for span in soup.find_all('span', {'class' : 'titolo51'}):
			if 'CODICE IMMOBILE:' in span.get_text():
				span_next = span.find_next_sibling('span', {'class' : 'titolo6'})
				if span_next:
					code = span_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					code = code[0] if code else ''
					property_obj.set_code(code)
		for td in soup.find_all('td'):
			if 'Superficie:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella'})
				if td_next:
					area = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					area = area[0] if area else ''
					property_obj.set_area(area)
			elif 'Costo:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella'})
				if td_next:
					price = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					price = price[0] if price else ''
					property_obj.set_price(price)
		for td in soup.find_all('td', {'class' : 'cella51'}):
			if 'Piani:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella61'})
				if td_next:
					max_floor = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					max_floor = max_floor[0] if max_floor else ''
					property_obj.set_max_floor(max_floor)
			elif 'Locali:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella61'})
				if td_next:
					rooms = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					rooms = rooms[0] if rooms else ''
					property_obj.set_rooms(rooms)
			elif 'Ascensore:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella61'})
				if td_next:
					elevator = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					elevator = elevator[0] if elevator else ''
					property_obj.set_elevator(elevator)
			elif 'Garage/Box:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella61'})
				if td_next:
					box = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					box = box[0] if box else ''
					property_obj.set_box(box)
		for td in soup.find_all('td', {'class' : 'cella5'}):
			if 'Piano:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella6'})
				if td_next:
					floor = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					floor = floor[0] if floor else ''
					property_obj.set_floor(floor)
			elif 'Balcone:' in td.get_text():
				td_next = td.find_next_sibling('td', {'class' : 'cella6'})
				if td_next:
					balcony = td_next.get_text().strip().replace('\\t', '').replace('\\n', '').split()
					balcony = balcony[0] if balcony else ''
					property_obj.set_balcony(balcony)
		return property_obj
	return None


def parse_page(page_html, filter_obj):
	empty_page = True
	if page_html:
		soup = BeautifulSoup(page_html, 'html.parser')
		for imm_table in soup.find_all('table', {'class' : 'imm'}):
			for imm_tr in imm_table.find_all('tr', {'class' : 'imm'}):
				for imm_a in imm_tr.find_all('a', {'class' : 'citta'}):
					if empty_page:
						empty_page = False
					imm_href = imm_a.get('href')
					if validators.url(imm_href):
						imm_html = get_html(casedavedere_host, imm_href)
						property_obj = parse_imm(imm_href, imm_table, imm_html)
						if property_obj and filter_obj.pass_filter(property_obj):
							code = property_obj.get_code()
							if code not in property_dict:
								print('Property Code: ' + str(code))
								property_dict[code] = property_obj
								property_list.append(property_obj)
	return empty_page


#######################################
# FUNZIONI DI GESTIONE DEL TERRITORIO #
#######################################

def get_provinces_and_municipalities():
	provinces_and_municipalities = []
	if os.path.isfile('provinces_and_municipalities.json'):
		with open('provinces_and_municipalities.json', 'r') as file:
			data = json.load(file)
			for province in data['SELECTED'].keys():
				for municipality in data['SELECTED'][province]:
					provinces_and_municipalities.append('{0}-{1}'.format(municipality, province))
	return provinces_and_municipalities


#################################################
# FUNZIONI DI GESTIONE DEGLI INDIRIZZI DI POSTA #
#################################################

def get_email_list():
	email_list = []
	if os.path.isfile('email_list.json'):
		with open('email_list.json', 'r') as file:
			data = json.load(file)
			for email in data['email']:
				email_list.append(email)
	return email_list


###################################
# FUNZIONI DI GESTIONE DEL FILTRO #
###################################

def get_property_filter():
	if os.path.isfile('property_filter.json'):
		with open('property_filter.json', 'r') as file:
			data = json.load(file)
			return PropertyFilter(
				min_area=int(data['min_area']),
				max_area=int(data['max_area']),
				min_price=int(data['min_price']),
				max_price=int(data['max_price']),
				int_floor=bool(data['intermediate_floor']),
				min_rooms=int(data['min_rooms']),
				min_balconies=int(data['min_balconies']),
				box=bool(data['need_box']),
				elevator=bool(data['need_elevator'])
			)
	return None


################################
# FUNZIONI DI GENERAZIONE HTML #
################################

def create_html_file(filter_obj):
	current_date = datetime.now()
	with open(filtered_property, 'w') as file:
		file.write('<!DOCTYPE html>\n')
		file.write('<html lang="it">\n')
		file.write(' <meta charset="UTF-8">\n')
		file.write(' <title>Case Da Vedere</title>\n')
		file.write(' <style>\n')
		file.write('  html, body { text-align : center; font-family : "Verdana", sans-serif }\n')
		file.write('  h1, h2, h3, h4, h5, h6 { font-family : "Segoe UI", sans-serif }\n')
		file.write('  table.filter { margin-left : auto; margin-right : auto }\n')
		file.write('  table.counter { margin-left : auto; margin-right : auto }\n')
		file.write('  table.imm { background-color : #D4EBF2; border : 1px solid black; border-collapse : collapse; margin-left : auto; margin-right : auto }\n')
		file.write(' </style>\n')
		file.write(' <body>\n')
		file.write('<h1>Case Da Vedere</h1>\n')
		file.write('<h3>[{0}]</h3>\n'.format(current_date.strftime("%d/%m/%Y %H:%M:%S")))
		file.write('<br>\n')
		file.write(filter_obj.stamp_filter())
		file.write('<br>\n')
		file.write('<table class="counter">\n')
		file.write(' <tr><th>Trovati:</th></tr>\n')
		file.write(' <tr><td>{0}</td></tr>\n'.format(len(property_list)))
		file.write('</table>\n')
		file.write('<br><br>\n')
		for property_obj in property_list:
			file.write(property_obj.get_html().prettify().replace('\\t', '').replace('\\n', ''))
			file.write('<br>\n')
		file.write(' </body>\n')
		file.write('</html>')


def create_html_string():
	current_date = datetime.now()
	html_string  = '<!DOCTYPE html>\n'
	html_string += '<html lang="it">\n'
	html_string += ' <meta charset="UTF-8">\n'
	html_string += ' <title>Case Da Vedere</title>\n'
	html_string += ' <style>\n'
	html_string += '  html, body { text-align : center; font-family : "Verdana", sans-serif }\n'
	html_string += '  h1, h2, h3, h4, h5, h6 { font-family : "Segoe UI", sans-serif }\n'
	html_string += '  table.filter { margin-left : auto; margin-right : auto }\n'
	html_string += '  table.counter { margin-left : auto; margin-right : auto }\n'
	html_string += '  table.imm { background-color : #D4EBF2; border : 1px solid black; border-collapse : collapse; margin-left : auto; margin-right : auto }\n'
	html_string += ' </style>\n'
	html_string += ' <body>\n'
	html_string += '<h1>Case Da Vedere</h1>\n'
	html_string += '<h3>[{0}]</h3>\n'.format(current_date.strftime("%d/%m/%Y %H:%M:%S"))
	html_string += '<br>\n'
	html_string += filter_obj.stamp_filter()
	html_string += '<br>\n'
	html_string += '<table class="counter">\n'
	html_string += ' <tr><th>Trovati:</th></tr>\n'
	html_string += ' <tr><td>{0}</td></tr>\n'.format(len(new_property_list))
	html_string += '</table>\n'
	html_string += '<br><br>\n'
	for property_obj in new_property_list:
		html_string += property_obj.get_html().prettify().replace('\\t', '').replace('\\n', '')
		html_string += '<br>\n'
	html_string += ' </body>\n'
	html_string += '</html>'
	return html_string


######################################
# FUNZIONI DI NOTIFICA NUOVI ANNUNCI #
######################################

def get_gmail_auth_token():
	credentials = None
	gmail_scopes = [
		'https://www.googleapis.com/auth/gmail.compose',
		'https://www.googleapis.com/auth/gmail.readonly'
	]
	if os.path.exists('token.json'):
		credentials = Credentials.from_authorized_user_file('token.json', gmail_scopes)
	if not credentials or not credentials.valid:
		if credentials and credentials.expired and credentials.refresh_token:
			credentials.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file('credentials.json', gmail_scopes)
			credentials = flow.run_local_server(port=0)
		with open('token.json', 'w') as token:
			token.write(credentials.to_json())
	return credentials


def create_gmail_html(sender, recipients, subject, text):
	message = MIMEText(text, 'html')
	message['to'] = recipients[0]
	for recipient in recipients[1:]:
		message['to'] += ',' + recipient
	message['from'] = sender
	message['subject'] = subject
	return { 'raw' : base64.urlsafe_b64encode(message.as_string().encode()).decode() }


def self_send_gmail(gmail_service, gmail_credentials, gmail_message):
	try:
		gmail_service.users().messages().send(userId='me', body=gmail_message).execute()
	except HttpError as error:
		print('Unable to send email: {0}'.format(error))


def check_new_properties():
	old_code_set = set()
	new_code_set = set(property_dict.keys())
	if os.path.isfile(property_code):
		with open(property_code, 'r') as file:
			for line in file:
				code = line.strip()
				old_code_set.add(code if code != 'None' else None)
	if new_code_set != old_code_set:
		with open(property_code, 'w') as file:
			for code in new_code_set:
				file.write(code if code else 'None')
				file.write('\n')
		for code in new_code_set.difference(old_code_set):
			new_property_list.append(property_dict[code])
	if new_property_list:
		email_list = get_email_list()
		if email_list:
			gmail_credentials = get_gmail_auth_token()
			gmail_service = build('gmail', 'v1', credentials=gmail_credentials)
			gmail_address = gmail_service.users().getProfile(userId='me').execute()['emailAddress']
			gmail_message = create_gmail_html(
	 			gmail_address,
	 			email_list,
	 			'CaseDaVedere',
	 			create_html_string(),
			)
			self_send_gmail(gmail_service, gmail_credentials, gmail_message)


############################
# ENTRY-POINT DELLO SCRIPT #
############################

if __name__ == '__main__':
	if resolve_hostname(casedavedere_host):
		filter_obj = get_property_filter()
		if filter_obj:
			provinces_and_municipalities = get_provinces_and_municipalities()
			for municipality_province in provinces_and_municipalities:
				page_num = 1
				while True:
		 			page_html = get_html(casedavedere_host, casedavedere_url.format(municipality_province, page_num))
		 			print('Page Number: ' + str(page_num))
		 			if parse_page(page_html, filter_obj):
						 break
		 			page_num += 1
			create_html_file(filter_obj)
			check_new_properties()