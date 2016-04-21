# -*- coding: utf-8 -*-
import requests
import re
import collections

from bs4 import BeautifulSoup as bs
from datetime import date, timedelta


class VacancyChecker:

    def __init__(self):
        self.base_url = 'https://www.keyakinet.jp'
        self.last_url = self.base_url + '/reselve/k_index.do'

        self.TIMESLOTS = ['morning', 'noon', 'afternoon', 'evening', 'night']
        self.free_slots = collections.OrderedDict()

        self.headers = {'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept-Encoding': 'gzip, deflate, sdch',
                        'Accept-Language': 'ja,en-US;q=0.8,en;q=0.6,cs;q=0.4',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36',
                        'Cache-Control': 'max-age=0',
                        'Connection': 'keep-alive'
                        }

    def get_token_data(self, content, params={}):
        token_name = 'org.apache.struts.taglib.html.TOKEN'
        soup = bs(content, 'html.parser')
        token = str(soup.find_all('input', {'name': token_name})[0]['value'])
        data = {token_name: token}

        for key, val in params.items():
            data[key] = val

        return data

    def post_request(self, last_response, url, parameters={}):
        # set cookie
        if not self.headers.get('Cookie'):
            cookie_name = 'JSESSIONID'
            cookie_val = last_response.cookies.get(cookie_name)
            self.headers['Cookie'] = cookie_name + "=" + cookie_val

        # load last url, set as referer, create current url and save as last
        self.headers['Referer'] = self.last_url
        curr_url = self.base_url + url
        self.last_url = curr_url

        # execute request
        return requests.post(curr_url,
                             headers=self.headers,
                             data=self.get_token_data(last_response.content,
                                                      parameters)
                             )

    def append_free_slots(self, r, school_name, fac_name):
        soup = bs(r.content, "html.parser")
        day_tds = soup.find_all('td', {'class': re.compile('^KOMASTS')})

        # find starting date of this week and create a month - day tuple
        start_date_jp = soup.find('div', {'id': 'DAY1'}).find('div', {'class': 'DAYTX'}).find('font').string.strip()
        start_date = (int(start_date_jp.split(u'月')[0]), int(start_date_jp.split(u'月')[1].split(u'日')[0]))

        # create date object from tuple
        year = date.today().year
        month = date.today().month
        # add 1 to year if month lower than month today
        if month > start_date[0]:
            year += 1
        start_full_date = date(year, start_date[0], start_date[1])

        for day_idx, day_td in enumerate(day_tds):
            # gif for past days: /reselve/IMAGES/kimg_ptnw_de.gif
            # gif for NG days: /reselve/IMAGES/kimg_ptnw_ng.gif
            # gif for OK days: /reselve/IMAGES/kimg_ptnw_ok.gif
            img = day_td.find_all('img', {'src': '/reselve/IMAGES/kimg_ptnw_ok.gif'})

            if len(img) > 0:
                if school_name not in self.free_slots.keys():
                    self.free_slots[school_name] = {}

                if fac_name not in self.free_slots[school_name].keys():
                    self.free_slots[school_name][fac_name] = []

                curr_date = start_full_date + timedelta(days=day_idx/5)

                self.free_slots[school_name][fac_name].append({
                    "date": str(curr_date),
                    "slot": self.TIMESLOTS[day_td.parent.index(day_td) / 2]
                })

        next_week = len(soup.find_all('input', {'id': 'NEXTWEEKBTN'})) > 0
        return next_week

    def do_check(self):
        # Index screen
        r = requests.get(self.last_url, self.headers)

        # Select Search method
        r = self.post_request(r, '/reselve/k_SelSearchPtn.do',
                              {'rsvtyp': '1',
                               'srhflg': '0'})

        # Select type of activity
        r = self.post_request(r, '/reselve/k_CtgSelInitial.do',
                              {'rsvptnflg': '1',
                               'rsvtyp': '1',
                               'changeflg': '0'}
                              )

        # Select from indoor sports
        r = self.post_request(r, '/reselve/k_PrpCtgSelInitial.do',
                              {'prptyp': '15',
                               'startindex': '0',
                               'prptypflg': '3',
                               'rsvptnflg': '1',
                               'prpstsflg': '0',
                               'prpmvflg': '0'}
                              )

        # Select type of indoor sport
        r = self.post_request(r, '/reselve/k_GovSelInitial.do',
                              {'prpcod': '3080',
                               'startindex': '0',
                               'prptypflg': '3',
                               'rsvptnflg': '1',
                               'prpstsflg': '1',
                               'prpmvflg': '0'}
                              )


        # dummy list for while loop purposes
        next_button = ["dummy"]
        startindex = 0

        # do while there is a next button on the school selection page
        while len(next_button) > 0:

            # Select area
            url = '/reselve/k_FacSelInitial.do'

            if startindex == 0:
                parameters = {'rgnide': 'XX',
                              'startindex': str(startindex),
                              'rsvptnflg': '1'}
            else:
                parameters = {'startindex': str(startindex),
                              'selIndex': '0'}

            r = self.post_request(r, url, parameters)

            next_button = bs(r.content, "html.parser").find_all('input', {'src': '/reselve/IMAGES/kbtn_fac_next.gif'})

            # Get divs for all schools displayed
            school_divs = bs(r.content, "html.parser").find_all('div', {'class': 'SEL'})

            # update start index for school listing
            startindex += len(school_divs)

            for school_div in school_divs:
                school_code = school_div['onclick'].replace("facSel('", '').replace("')", '')
                school_name = school_div.find('div', {'class': 'SELTXT'}).string

                url = '/reselve/k_ObjSelInitial.do'
                parameters = {'facide': str(school_code.strip()),
                              'startindex': '0',
                              'rsvptnflg': '1',
                              'selIndex': '0'}

                r = self.post_request(r, url, parameters)

                # Get divs for all facilities displayed
                fac_divs = bs(r.content, "html.parser").find_all('div', {'class': 'SEL'})

                for fac_div in fac_divs:
                    fac_code = fac_div['onclick'].replace("objSel('", '').replace("')", '')
                    fac_name = fac_div.find('div', {'class': 'SELTXT'}).string

                    url = '/reselve/k_ObjRsvListInitial.do'

                    # The last character of the facility code is used as an object type marker
                    parameters = {'objide': str(fac_code.strip()[:-1]),
                                  'objtyp': str(fac_code.strip()[-1:]),
                                  'startindex': '0'}

                    r = self.post_request(r, url, parameters)

                    next_week = self.append_free_slots(r, school_name, fac_name)

                    # repeat until no next week button
                    while next_week:
                        r = self.post_request(r, url,
                                              {'dateFlg': '2'})

                        next_week = self.append_free_slots(r, school_name, fac_name)

                    # return to facility selection
                    url = '/reselve/k_ObjSelInitial.do'
                    r = self.post_request(r, url,
                                          {'selIndex': '0'})

                # return to school selection
                url = '/reselve/k_FacSelInitial.do'
                r = self.post_request(r, url,
                                      {'startindex': '0',
                                       'objtyp': '1'})

        return self.free_slots
