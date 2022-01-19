#!/usr/bin/python3
# coding: utf8
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate
import smtplib
from datetime import datetime, date, time, timedelta
import requests
import shutil
import os
import argparse
import socket
import re
import binascii

# Location for Temporary files
TEMP = '/tmp/'

    # v1.1 - Added Static Panel Renderer URL Path segment as a parameter (-Z)
    #        In the latest version of Grafana renderer a unique element is added to the URL for each dashboard
    #        and this must be inserted into the renderer request URL

    # Daily Level Report parameter example
    # min stat - ('water-24h-view',6,400,100)
    # max stat - ('water-24h-view',8,400,100)
    # graph    - ('water-24h-view',2,800,400)
    # alerts   - ('water-24h-view',4,800,150)

    # HTML Template Example
    # |------------------|
    # |   Min   |  Max   |
    # |------------------|
    # |    Main Graph    |
    # |------------------|
    # |      Alerts      |
    # |------------------|

    #<html>
    #    <body>
    #       <p>Daily Tank Level Report for last 24 hours.<br>
    #       <table>
    #           <tr>
    #               <td> <img src="cid:img_water-24h-view-6.png" alt="Minimum Tank Level"> </td>
    #               <td> <img src="cid:img_water-24h-view-8.png" alt="Maximum Tank Level"> </td>
    #           </tr>
    #           <tr>
    #               <td  colspan="2"> <img src="cid:img_water-24h-view-2.png" alt="Tank Level Chart"> </td>
    #           </tr>
    #           <tr>
    #               <td  colspan="2"> <img src="cid:img_water-24h-view-4.png" alt="Alerts"> </td>
    #           </tr>
    #       </table>
    #    </body>
    #</html>

# indexes of the fields for the panel definition tuple.
# (<dashboard>,<panel_id>,<width>,<height>)
DASHBOARD = 0
PANEL_ID = 1
WIDTH = 2
HEIGHT = 3

def mail_type(s):
    if not re.match(r"[^@^\s]+@[^@^\s]+\.[^@\s]+", s):
         raise argparse.ArgumentTypeError('The mail is not a valid email')
    return s

def panel_type(s):
    try:
        #strip the brackets from the panel tuple
        s = s.replace("(", "")
        s = s.replace(")", "")

        dashboard, panelId, width, height = s.split(',')

        try:
            y = int(panelId)
        except ValueError:
            raise argparse.ArgumentTypeError("PanelId must be an integer: [" + s + "]")
        try:
            y = int(width)
        except ValueError:
            raise argparse.ArgumentTypeError("Width must be an integer: [" + s + "]")
        try:
            y = int(height)
        except ValueError:
            raise argparse.ArgumentTypeError("Height must be an integer: [" + s + "]")
    except:
         raise argparse.ArgumentTypeError("Every panel must be (<str>dashboard,<int>panelId,<int>width,<int>height): [" + s + "]")
    return dashboard, panelId, width, height

def parse_args():
    parser = argparse.ArgumentParser(
        description='Email a custom report based on Grafana dashboard panels + HTML Template',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--mail_from",
                    dest="mail_from",
                    type=mail_type,
                    help="Mail from address.",
                    required=False)
    parser.add_argument("-S", "--subjectline",
                    dest="subject_line", type=str,
                    help="Mail Subject line.",
                    required=True)
    parser.add_argument("-H", "--html_template",
                    dest="template_file", type=str,
                    help="HTML e-mail template file.",
                    required=True)
    parser.add_argument("-m", "--mail_list",
                    dest="mail_list",
                    nargs='+', type=mail_type,
                    help="Mail list, separed by space.",
                    required=True)
    parser.add_argument("-M", "--mailhost",
                    dest="mailhost", type=str,
                    help="Mailhost hostname or IP.",
                    required=True)
    parser.add_argument("-u", "--user",
                    dest="user", type=str,
                    help="Mail Server Login user ID.",
                    required=True)
    parser.add_argument("-p", "--password",
                    dest="password", type=str,
                    help="Mail Server Login Password.",
                    required=True)
    parser.add_argument("-G", "--grafana_server",
                    dest="grafana_server",
                    help="Grafana server & port, ex: http://grafana.test:3000",
                    required=True)
    parser.add_argument("-T", "--api_token",
                    dest="api_token", type=str,
                    help="Grafana API Token to access the dashboard.",
                    required=True)
    parser.add_argument("-Z", "--panel_token",
                    dest="panel_token", type=str,
                    help="Grafana static panel path to access the dashboard.",
                    required=True)
    parser.add_argument("-P", "--panel_list",
                    dest="panel_list",
                    nargs='+', type=panel_type,
                    help="Tuple of Grafana dashboard Id, panelId, width and height; every tuple has to be separated by a space, ex ('test',1,400,100) ('dashboard2',15,400,100) ...",
                    required=True)
    return parser.parse_args()

def prepare(from_addr, subject_line, template_file):
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] =  subject_line
    msgRoot['From'] = '<' + from_addr + '>'
    msgRoot['Date'] = formatdate()
    msgRoot['Message-ID'] = '<' + str(binascii.b2a_hex(os.urandom(15))) + '@' + from_addr + '>'
    print(msgRoot['Message-ID'])
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    msgAlternative = MIMEMultipart('alternative')

    msgTemplate = load_template(template_file)
    msgText = MIMEText(msgTemplate, 'html')

    msgAlternative.attach(msgText)

    msgRoot.attach(msgAlternative)

    return msgRoot

def create_filename(dashboard, panelId):
    return 'img_' + dashboard + '-' + panelId + '.png'

def download(grafana_server, dashboard, panelId, width, height, img_file, api_token, panel_token):
    url = (grafana_server + '/render/d-solo/' + panel_token + '/' + dashboard +
            '?panelId=' + panelId +
            '&width=' + width +
            '&height=' + height +
            '&theme=light'
            )
    print(url)
    r = requests.get(url, headers={"Authorization": "Bearer " + api_token}, stream=True)
    if r.status_code == 200:
        with open(TEMP + img_file, 'wb') as picture:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, picture)
    del r

def send(msgRoot, mail_list, mailhost, user, password, strFrom):
    msgRoot['To'] = ", ".join(mail_list)
    smtp = smtplib.SMTP()
    smtp.connect(mailhost, 25)
    smtp.login(user, password)
    smtp.sendmail(strFrom, mail_list, msgRoot.as_string())
    smtp.quit()

def attach_img(msgRoot, img_name):
    fp = open(TEMP + img_name, 'rb')
    msgImage = MIMEImage(fp.read(), _subtype="png")
    fp.close()

    msgImage.add_header('Content-ID', '<' + img_name + '>')
    msgImage.add_header('Content-Disposition', 'attachment;filename="' + img_name + '"')
    msgRoot.attach(msgImage)

def load_template(template_file):
    template_text = ""

    with open(template_file, 'r') as template:
        template_text = template.read()
    return template_text


if __name__ == '__main__':
    args = parse_args()
    if args.mail_from:
        strFrom = args.mail_from
    else:
        strFrom = socket.getfqdn()

    msgRoot = prepare(strFrom, args.subject_line, args.template_file)

    # fetch and attach all the images, delete images after they are attached
    for panel in args.panel_list:
        # print(panel)
        img_name = create_filename(panel[DASHBOARD], panel[PANEL_ID])
        download(args.grafana_server, panel[DASHBOARD], panel[PANEL_ID], panel[WIDTH], panel[HEIGHT], img_name, args.api_token, args.panel_token )
        attach_img(msgRoot, img_name)
        # tidy up the temporary file
        os.remove(TEMP + img_name)

    # Send one email to all listed recipients
    send(msgRoot, args.mail_list, args.mailhost, args.user, args.password, strFrom)