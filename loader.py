# -*- encoding: utf-8 -*-

from pcms import PCMS
pcms = PCMS()
pcms.login()
all_jobs = pcms.get_jobs()

def total_time_for_all_tests(tests):
    ret = 0
    for test in tests:
        tokens = test['time'].split()
        time = int(''.join(tokens[:-1]))
        units = tokens[-1]
        time *= {'ms': 0.001, 's': 1}[units]
        ret += time
    return ret


C_set = ['c.gnu', 'c.gnu.linux.lm', 'c.visual', 'cpp.gnu.linux', 'cpp.visual', 'cpp11.gnu']
java_set = ['java.sun']

fltr = lambda x: x['languageId'] in C_set and x['shortOutcome'] == 'OK' and x['problemAlias'] == 'A'

jobs_by_language = list(filter(fltr, all_jobs))


jobs_filtered = []
for job in jobs_by_language:
    flag = True
    for jf in jobs_filtered:
        if jf['partyName'] == job['partyName']:
            flag = False
            jf_tests = pcms.get_tests_for_job(jf)
            job_tests = pcms.get_tests_for_job(job)

            jf_time = total_time_for_all_tests(jf_tests)
            job_time = total_time_for_all_tests(job_tests)

            if jf_time > job_time:
                jobs_filtered.remove(jf)
                flag = True
            break
    if flag:
        jobs_filtered.append(job)



print(len(jobs_filtered))

for job in jobs_filtered:
    name = job['partyName']
    name = name.replace('.', '_')

    path = 'cpp_submissions/{0}.cpp'.format(name)
    with open(path, 'w') as f:
    #with open(path, 'w', encoding='utf-8') as f:
        code = pcms.get_code(job)
        try:
            f.write(code)
        except:
            continue