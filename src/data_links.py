# Fall data
fall_trans ="https://drive.google.com/file/d/1Q4G-RJAXd0GgkCyJpA8ajTXTk0hOyQhe/view?usp=drive_link"
fall_lab_data="https://drive.google.com/file/d/1_lj9joFbkBjqZOXT7z7-q2AkFbc6sJez/view?usp=drive_link"
fall_consent="https://drive.google.com/file/d/1OBOz23ByNoxk7L2-DMKa3rhR_U9G56b-/view?usp=drive_link"
fall_grades="https://drive.google.com/file/d/1sOAi7UKfeYjv_l6DjsHfMbEQJbK4p9Hz/view?usp=drive_link"
fall_user="https://drive.google.com/file/d/1TGJ-6OP2ig5eQeT8722i6VOn2-g250di/view?usp=drive_link"
fall_survey="https://drive.google.com/file/d/1J_k6_tVPGf5lY6Pm2YoeKzm-WGwlFd8C/view?usp=drive_link"

# Winter data
winter_trans ="https://drive.google.com/file/d/1rrv-K6od2GkgIw6GXeL-r0RvCaHMkZ9-/view?usp=drive_link"
winter_lab_data="https://drive.google.com/file/d/1ozuoubIwzG5Pl13_pyAanDly0AH4rMwb/view?usp=drive_link"
winter_consent="https://drive.google.com/file/d/1wjpPGcbnFkO0tAOvwW5z-Isac4DVzPcv/view?usp=drive_link"
winter_grades="https://drive.google.com/file/d/1XZExc-91llQyHMWPQ-pKqOeM0-mVi1gI/view?usp=drive_link"
winter_user="https://drive.google.com/file/d/1oOynEqjAoQlhaK-tKtZTC2ZrkMnHj_hk/view?usp=drive_link"
winter_survey="https://drive.google.com/file/d/1Zv0du5gBrbhRrXb5KuSqRotEcZMEJJL2/view?usp=drive_link"

# Spring data
spring_trans =""
spring_lab_data=""
spring_consent=""
spring_grades=""
spring_user=""
spring_survey=""


## Defines term links. returns link_dict, str(error)
def term_return(term): # fall, winter, spring
    if term == "fall":
        links ={
            "trans":fall_trans,
            "lab_data":fall_lab_data,
            "consent":fall_consent,
            "grades":fall_grades,
            "user":fall_user,
            "survey":fall_survey,
        }
    elif term == "winter":
        links ={
            "trans":winter_trans,
            "lab_data":winter_lab_data,
            "consent":winter_consent,
            "grades":winter_grades,
            "user":winter_user,
            "survey":winter_survey,
        }
    else:
        return {}, "No valid term defined."
    return links, None

import sys
term = sys.argv[1]
links, error = term_return(term)

print(error, links)