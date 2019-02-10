# -*- encoding: utf-8 -*-

from configparser import ConfigParser
import os
import requests
from bs4 import BeautifulSoup


class PCMS:
    def __init__(self):
        config = self._read_config()
        self.base_url = config['server']
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        self.username = config['username']
        self.password = config['password']
        self.site_id = config['site_id']
        self.contest_id = config['contest_id']
        self.session = None

    def login(self):
        url = '{}pcms2client/login.xhtml'.format(self.base_url)
        if self.session is not None:
            self.logout()
        self.session = requests.session()
        r = self.session.get(url)
        self._check_response(r)
        cookie = self._parse_java_csrf(r)

        r = self.session.post(url, data={
            'login': 'login',
            'login:name': self.username,
            'login:password': self.password,
            'login:submit': 'Login',
            cookie[0]: cookie[1]
        })
        self._check_response(r)
        self.set_locale('en')

    def logout(self):
        url = '{}pcms2client/logout.xhtml'.format(self.base_url)
        self.session.get(url)
        del self.session
        self.session = None

    def set_contest(self, contest_id):
        url = '{}pcms2client/contests.xhtml'.format(self.base_url)
        r = self.session.get(url)
        self._check_response(r)
        cookie = self._parse_java_csrf(r)
        magic = 'j_idt25:j_idt26:{}:j_idt28'.format(contest_id)
        r = self.session.post(url, data={
            'j_idt25': 'j_idt25',
            magic: magic,
            cookie[0]: cookie[1]
        })
        self._check_response(r)

    def get_jobs(self):
        url = '{}pcms2client/admin/dump.xhtml'.format(self.base_url)
        r = self.session.get(url, params={
            'site': self.site_id
        })
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.html.body.table
        # header = [th.text for th in table.thead.tr.find_all('th')]
        jobs = []
        for tr in table.find_all('tr', recursive=False):
            job = {}
            for td in tr.find_all('td'):
                job[td['class'][0]] = td.text
            jobs.append(job)
        return jobs

    def get_tests_for_job(self, job):
        url = '{}pcms2client/admin/job.xhtml'.format(self.base_url)
        session_id = '{contest_id}.{sessionId}'.format(
            contest_id=self.contest_id, **job)
        job_id = '{contest_id}.{sessionId}.{problemAlias}.{attempt}.{job}'.format(
            contest_id=self.contest_id, **job)
        r = self.session.get(url, params={
            'site': self.site_id,
            'session-id': session_id,
            'job-id': job_id
        })

        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.html.find(class_='checkerComment').parent.parent
        assert table.name == 'table'
        tests = []
        for tr in table.find_all('tr', recursive=False):
            if tr.get('class', ['meta'])[0] != 'meta':
                test = {}
                for td in tr.find_all('td'):
                    if ' '.join(td['class']) != 'show link':
                        test[td['class'][0]] = td.text
                test['time'] = test['time'].replace('\xa0', ' ')
                tests.append(test)
        return tests

    def get_code(self, job):
        url = '{}pcms2client/admin/job.xhtml'.format(self.base_url)
        session_id = '{contest_id}.{sessionId}'.format(
            contest_id=self.contest_id, **job)
        job_id = '{contest_id}.{sessionId}.{problemAlias}.{attempt}.{job}'.format(
            contest_id=self.contest_id, **job)
        r = self.session.get(url, params={
            'site': self.site_id,
            'session-id': session_id,
            'job-id': job_id
        })

        soup = BeautifulSoup(r.text, 'html.parser')
        pre = soup.html.find('pre', class_='source')
        code = pre.text
        return code


    def set_locale(self, locale):
        url = '{}pcms2client/information.xhtml'.format(self.base_url)
        r = self.session.get(url)
        self._check_response(r)
        cookie = self._parse_java_csrf(r)

        r = self.session.post(url, data={
            'locale': 'locale',
            'locale:name': locale,
            cookie[0]: cookie[1]
        })
        self._check_response(r)

    @staticmethod
    def _parse_java_csrf(r):
        soup = BeautifulSoup(r.text, 'html.parser')
        node = None
        for idx in range(10):
            node = soup.html.find(id='j_id1:javax.faces.ViewState:{}'.format(idx))
            if node is not None:
                break
        return node['name'], node['value']

    @staticmethod
    def _read_config(config_file=None):
        if config_file is None:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            config_file = os.path.join(script_dir, 'config.ini')
        config = ConfigParser()
        config.read_file(open(config_file))
        return config['DEFAULT']

    @staticmethod
    def _check_response(r):
        if r.status_code > 400:
            raise RuntimeError('Got response {} from server'.format(r.status_code))