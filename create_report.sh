python graf-report.py -f <from e-mail> -m <to e-mail> -S "Weekly Max-Min Tank Level Report." -M <mail server> --user <user> --password <password> -G http://grafana.local:3000 -H weekly-max-min.html -P \("weekly-max-min-azure",6,400,100\) \("weekly-max-min-azure",4,400,100\) \("weekly-max-min-azure",2,800,400\) -T <API Token>