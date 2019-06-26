"""
Definition of views.
"""

from django.shortcuts import render, HttpResponseRedirect
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
import urllib
from django.http import JsonResponse
from django.template import RequestContext
from django.views.generic.edit import CreateView
from django.http import HttpResponse
from datetime import datetime
from app.forms import ProfileForm
from app.forms import Profile
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from django.conf import settings
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import requests
import json,os
import time
import tweepy
import sqlite3
import reportlab
from fuzzywuzzy import fuzz
from difflib import SequenceMatcher

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(request,
        'app/index.html',
        {
            'title':'Home Page',
            'year':datetime.now().year,
        })

# SignIn to Linkedin
def SignIn(EmailAddress,Password):
    LoginDone = False
    print("\t\t\t-----------------------")
    print("\t\t\t  Requesting Linkedin  ")
    print("\t\t\t-----------------------")
    URL = 'https://www.linkedin.com/uas/login'
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0',
              'From': EmailAddress}
    session = requests.session()
    login_response = session.get('https://www.linkedin.com/uas/login', headers=header)
    login = BeautifulSoup(login_response.text, 'html.parser')

    # Get hidden form inputs
    inputs = login.find('form', {'class': 'login__form'}).findAll('input')

    # Create POST data
    post = {input.get('name'): input.get('value') for input in inputs}
    post['session_key'] = EmailAddress
    post['session_password'] = Password

    # Post login
    post_response = session.post('https://www.linkedin.com/uas/login-submit', data=post, headers=header)

    # Get home page
    home_response = session.get('http://www.linkedin.com/nhome', headers=header)
    Owner_First = ""
    Owner_Last = ""
    Owner_Public = ""
    Owner_Occu = ""
    if home_response.status_code == 200:
        Soup = BeautifulSoup(home_response.content, 'html.parser')
        CodeIdGetter = Soup.findAll("code")
        CodeLen = len(CodeIdGetter)
        # Finding Person Automated Data
        DataId = ""
        if len(CodeIdGetter) > 1:
            for C in CodeIdGetter:
                Id = str(C.get("id"))
                if not Id.__contains__("datalet"):
                    if Id.__contains__("bpr-guid"):
                        Data = Soup.find("code", {"id": str(Id)})
                        if Data.text.__contains__("premiumSubscriber"):
                            LoginDone = True
                            DataId = Id
                        pass
                    pass
                pass
            pass
        pass
        if LoginDone:
            print("\t\t\t----------------------")
            print("\t\t\t  Login Successfully  ")
            print("\t\t\t----------------------")
            CodeData = Soup.findAll("code", {"id": str(DataId)})
            for C in CodeData:
                CodeData = C.text
            pass
            JsonData = json.loads(CodeData)
            TotalLength = 0
            while TotalLength < JsonData['included'].__len__():
                if str(JsonData['included'][TotalLength]).__contains__("firstName"):
                    Owner_First = str(JsonData['included'][TotalLength]['firstName'])
                    print("First Name:{}".format(Owner_First))
                if str(JsonData['included'][TotalLength]).__contains__("lastName"):
                    Owner_Last = str(JsonData['included'][TotalLength]['lastName'])
                    print("Last Name:{}".format(Owner_Last))
                if str(JsonData['included'][TotalLength]).__contains__("publicIdentifier"):
                    Owner_Public = str("https://www.linkedin.com/in/") + str(JsonData['included'][TotalLength]['publicIdentifier'])
                    print("Public Profile:{}".format(Owner_Public))
                if str(JsonData['included'][TotalLength]).__contains__("occupation"):
                    Owner_Occu = str(JsonData['included'][TotalLength]['occupation'])
                    print("Occupation:{}".format(Owner_Occu))
                pass
                TotalLength += 1
            pass
    return LoginDone,session,Owner_First,Owner_Last,Owner_Public,Owner_Occu
    pass

# Extracting Complete Profile Inforamtion
def GatherData(FirstName, LastName, CurrentOccupation, ProfileURL,session):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    Skills = []
    PostalCode = "" 
    CountryCode = ""
    ProfileOccupation = ""
    CroppedImage = ""
    Description = ""
    LocationName = ""
    Headline = ""
    Summary = ""
    IndustryName = ""
    SchoolName = ""
    CompanyName = ""
    SkillsName = ""
    print('\t\t\t  Searching:{} Profile  '.format(ProfileURL))
    if not str(ProfileURL).__contains__("UNKNOWN"):
        if not str(ProfileURL).__contains__("N/A"):
            if not str(ProfileURL).__contains__("#"):
                Result = session.get(ProfileURL, headers=header)
                if Result.status_code == 200:
                    Soup = BeautifulSoup(Result.content, 'html.parser')
                    CodesCollection = Soup.findAll("code")
                    ProfileID = ""
                    for C in CodesCollection:
                        Data = json.dumps(C.text)
                        if str(Data).__contains__("publicationView"):
                            ProfileID = C.get("id")
                        pass
                    pass
                    CodeContent = Soup.find("code", {"id": str(ProfileID)})
                    ProfileContent = ""
                    Converted = False
                    try:
                        ProfileContent = CodeContent.text
                        Converted = True
                    except:
                        try:
                            for C in CodeContent:
                                ProfileContent = C.text
                            pass
                            Converted = True
                        except:
                            print("Unable to Convert into Text")
                            Converted = False
                        pass
                    pass
                    if Converted:
                        ProfileContent = json.loads(ProfileContent)
                        SummaryData = ""
                        CurrentDescription = []
                        SName = []
                        CName = []
                        DName = []
                        FieldName = []
                        CTitle = []
                        Activity = []
                        for value, key in ProfileContent.items():
                            for k in key:
                                if str(k).__contains__("description"):
                                    if k.get('description'):
                                        CurrentDescription.append(k.get('description'))
                                        #print("Description:{}".format(k.get('description')))
                                        if k.get('companyName'):
                                            #print("Company Name:{}".format(k.get('companyName')))
                                            CName.append(k.get('companyName') + ",")
                                        pass
                                        if k.get('schoolName'):
                                            #print("School Name:{}".format(k.get('schoolName')))
                                            SName.append(k.get('schoolName') + ",")
                                        if k.get('degreeName'):
                                            #print("degreeName:{}".format(k.get('degreeName')))
                                            DName.append(k.get('degreeName') + ",")
                                        pass
                                        if k.get('fieldOfStudy'):
                                            #print("fieldOfStudy:{}".format(k.get('fieldOfStudy')))
                                            FieldName.append(k.get('fieldOfStudy') + ",")
                                        pass
                                        if k.get('activities'):
                                            #print("activities:{}".format(k.get('activities')))
                                            Activity.append(k.get('activities') + ",")
                                        pass
                                        if k.get('title'):
                                            #print("title:{}".format(k.get('title')))
                                            CTitle.append(k.get('title') + ",")
                                        pass
                                    pass
                                pass
                            pass
                            ConvertedData = CurrentDescription
                            Description = (unicode(ConvertedData), 'utf-8')
                            SchoolName = SName
                            CompanyName = CName
                            CompanyTitle = CTitle
                            DegreeName = DName
                            FieldStudy = FieldName
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__("headline"):
                                        Headline = ProfileContent['included'][Index]['headline']
                                        print("Headline:{}".format(Headline))
                                    pass
                                except:
                                    get = True
                                pass
                                Index += 1
                            pass
                            for value, key in ProfileContent.items():
                                for k in key:
                                    if str(k).__contains__("summary"):
                                        try:
                                            Summary = k.get('summary')
                                            #print("Summary:{}".format(Summary))
                                            break
                                        except:
                                            Summary = "N/A"
                                        pass
                                    pass
                                pass
                                if len(Summary) > 0:
                                    break
                                pass
                            pass
                            for value, key in ProfileContent.items():
                                for k in key:
                                    try:
                                        if str(k).__contains__("$type"):
                                            if str(k.get('$type')).__contains__('com.linkedin.voyager.identity.profile.Skill'):
                                                if k.get('name'):
                                                    print("Skills:{}".format(k.get('name')))
                                                    if not k.get('name') in Skills: 
                                                        Skills.append(k.get('name'))
                                                pass
                                            pass
                                        pass
                                    except:
                                        print(' ')
                                    pass
                                pass
                            pass
                            SkillsName = Skills
                            WorkHistory = []
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__("occupation"):
                                        occupation = str(ProfileContent['included'][Index]['occupation'])
                                        if not occupation.__contains__("urn:li:fs_"):
                                            WorkHistory.append(ProfileContent['included'][Index]['occupation'])
                                        pass
                                except:
                                    get = True
                                pass
                                Index += 1
                            pass
                            ProfileOccupation = WorkHistory
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__("countryCode"):
                                        CountryCode = ProfileContent['included'][Index]['countryCode']
                                        #print(CountryCode)
                                except:
                                    get = True
                                pass
                                Index += 1
                            pass
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__("postalCode"):
                                        PostalCode = ProfileContent['included'][Index]['postalCode']
                                        #print(PostalCode)
                                except:
                                    get = True
                                pass
                                Index += 1
                            pass
                            Location = ""
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__("locationName"):
                                        Location = ProfileContent['included'][Index]['locationName']
                                        print(ProfileContent['included'][Index]['locationName'])
                                except:
                                    get = True
                                pass
                                Index += 1
                            pass
                            LocationName = Location + "," + PostalCode + "," + CountryCode
                            RootUrl = ""
                            FakeImage = []
                            for value, key in ProfileContent.items():
                                if str(key).__contains__("fileIdentifyingUrlPathSegment"):
                                    for Image in str(key).split('fileIdentifyingUrlPathSegment'):
                                        if Image.__contains__('400_400/0'):
                                            FakeImage.append(
                                                str(Image).split(',')[0].replace("'", '').strip().replace(': u', ''))
                                        pass
                                    pass
                                    for Image in str(key).split('rootUrl'):
                                        if Image.__contains__('profile-displayphoto-shrink'):
                                            RootUrl = str(Image).split(',')[0].replace("'", '').strip().replace(': u',
                                                                                                                '').replace(
                                                '}', '')
                                        pass
                                    pass
                                pass
                            pass
                            PathStatement = FakeImage[-1]
                            if len(RootUrl) and len(PathStatement) is not 0:
                                #print("Profile Image:{}".format(RootUrl + PathStatement))
                                CroppedImage = RootUrl + PathStatement
                            else:
                                CroppedImage = 'N/A'
                            pass
                            Index = 0
                            get = False
                            while get is not True:
                                try:
                                    if str(ProfileContent['included'][Index]).__contains__('industryName'):
                                        IndustryName = ProfileContent['included'][Index]['industryName']
                                        #print(IndustryName)
                                        if len(IndustryName) > 0:
                                            break
                                        pass
                                except:
                                    IndustryName = 'N/A'
                                    get = True
                                pass
                                Index += 1
                            pass
                        pass
                    pass
                pass
            pass
        pass
        return FirstName, LastName, CurrentOccupation, ProfileURL, Headline, LocationName, IndustryName,Summary, Description, SchoolName, CompanyName, CroppedImage, ProfileOccupation, SkillsName,CompanyTitle,DegreeName,FieldStudy,Activity
    pass

# Extracting Basic Profile of Linkedin
def BasicProfile(NameList,TitleList,LocationList,session,Owner_First,Owner_Last,Owner_Pub,Owner_Occu,Person):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    Gat_FirstName = []
    Gat_LastName = [] 
    Gat_CurrentOccupation = []
    Gat_ProfileURL = []
    Gat_Headline = []
    Gat_LocationName = []
    Gat_IndustryName = []
    Gat_Summary = []
    Gat_Description = []
    Gat_SchoolName = []
    Gat_CompanyName = []
    Gat_CroppedImage = []
    Gat_ProfileOccupation = []
    Gat_SkillsName = []
    Gat_Title = []
    Gat_Degree = []
    Gat_StudyField = []
    Gat_Activity = []
    if Person == 0:
        A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R = GatherData(Owner_First, Owner_Last, Owner_Occu,Owner_Pub,session)
        Gat_FirstName.append(A)
        Gat_LastName.append(B)
        Gat_CurrentOccupation.append(C)
        Gat_ProfileURL.append(D)
        Gat_Headline.append(E)
        Gat_LocationName.append(F)
        Gat_IndustryName.append(G)
        Gat_Summary.append(H)
        Gat_Description.append(I)
        Gat_SchoolName.append(J)
        Gat_CompanyName.append(K)
        Gat_CroppedImage.append(L)
        Gat_ProfileOccupation.append(M)
        Gat_SkillsName.append(N)
        Gat_Title.append(O)
        Gat_Degree.append(P)
        Gat_StudyField.append(Q)
        Gat_Activity.append(R)
        return Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity
    else:
        FirstName = []
        LastName = []
        Occupation = []
        ProfileURL = []
        query = NameList.replace(" ", "%20") + "%20" + TitleList.replace(" ", "%20") + "%20" + LocationList.replace(" ", "%20")
        Searchquery = 'https://www.linkedin.com/search/results/people/?keywords=' + str(query) + '&origin=GLOBAL_SEARCH_HEADER'
        Result = session.get(Searchquery, headers=header)   
        Soup = BeautifulSoup(Result.content, 'html.parser')
        CodeIdGetter = Soup.findAll("code")
        CodeLen = len(CodeIdGetter)
        DataId = ""
        if len(CodeIdGetter) > 1:
            for C in CodeIdGetter:
                Id = str(C.get("id"))
                if not Id.__contains__("datalet"):
                    if Id.__contains__("bpr-guid"):
                        Data = Soup.find("code", {"id": str(Id)})
                        if Data.text.__contains__("metadata"):
                            DataId = Id
                        pass
                    pass
                pass
            pass
            CodeData = Soup.findAll("code", {"id": str(DataId)})
            for C in CodeData:
                CodeData = C.text
            pass
            JsonData = json.loads(CodeData)
            TotalLength = 0
            while TotalLength < JsonData['included'].__len__():
                if str(JsonData['included'][TotalLength]).__contains__("firstName"):
                    First = str(JsonData['included'][TotalLength]['firstName'])
                    if len(First) <= 1:
                        FirstName.append("N/A")
                    else:
                        FirstName.append(First)
                    pass
                if str(JsonData['included'][TotalLength]).__contains__("lastName"):
                    Last = JsonData['included'][TotalLength]['lastName']
                    if len(Last) <= 1:
                        LastName.append("N/A")
                    else:
                        LastName.append(Last)
                    pass
                if str(JsonData['included'][TotalLength]).__contains__("publicIdentifier"):
                    Public = str("https://www.linkedin.com/in/") + str(JsonData['included'][TotalLength]['publicIdentifier'].encode('ascii','ignore'))
                    if len(Public) <= 1:
                        ProfileURL.append("N/A")
                    else:
                        ProfileURL.append(Public)
                        print("publicIdentifier:{}".format(Public))
                    pass
                if str(JsonData['included'][TotalLength]).__contains__("occupation"):
                    Occu = str(JsonData['included'][TotalLength]['occupation'])
                    if len(Occu) <= 1:
                        Occupation.append("N/A")
                    else:
                        Occupation.append(Occu)
                    pass    
                pass
                TotalLength += 1
            pass
            New_FirstName = []
            New_LastName = []
            New_ProfileURL = []
            New_Occupation = []
            print('Total User:{}'.format(len(ProfileURL)))
            Checker = 0
            if len(ProfileURL) > 0:
                while Checker < len(ProfileURL):
                    s = SequenceMatcher(None, NameList.lower(),
                                        FirstName[Checker].lower() + " " + LastName[Checker].lower())
                    if s.ratio() >= 0.80:
                        print("\t\t\tName Match Ratio: %.2f" % s.ratio())
                        Loc = SequenceMatcher(None, TitleList.lower(), Occupation[Checker].lower())
                        if Loc.ratio() >= 0.10:
                            print("\t\t\tLocation Match Ratio: %.2f" % Loc.ratio())
                            New_FirstName.append(FirstName[Checker])
                            New_LastName.append(LastName[Checker])
                            New_ProfileURL.append(ProfileURL[Checker])
                            New_Occupation.append(Occupation[Checker])
                        else:
                            print('Profile Not Match')
                        pass
                    pass
                    Checker += 1
                pass
            pass
            if len(New_ProfileURL) > 0:
                Prof = 0
                while Prof < len(New_ProfileURL):
                    A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R = GatherData(New_FirstName[Prof], New_LastName[Prof], New_Occupation[Prof], New_ProfileURL[Prof],session)
                    Gat_FirstName.append(A)
                    Gat_LastName.append(B)
                    Gat_CurrentOccupation.append(C)
                    Gat_ProfileURL.append(D)
                    Gat_Headline.append(E)
                    Gat_LocationName.append(F)
                    Gat_IndustryName.append(G)
                    Gat_Summary.append(H)
                    Gat_Description.append(I)
                    Gat_SchoolName.append(J)
                    Gat_CompanyName.append(K)
                    Gat_CroppedImage.append(L)
                    Gat_ProfileOccupation.append(M)
                    Gat_SkillsName.append(N)
                    Gat_Title.append(O)
                    Gat_Degree.append(P)
                    Gat_StudyField.append(Q)
                    Gat_Activity.append(R)
                    Prof+=1
                pass
            pass
        return Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity
    pass
    pass

# Extracting Basic Data from Twitter
def GatherTwitterDetails(Twitter_ProfileLink,Summary):
    ProfileLink = []
    Profile_Username = []
    Profile_ID = []
    Profile_Location = []
    Profile_Image = []
    TwitterFollowers=[]
    TwitterFriend=[]
    Latest_Post = []
    Total = 0
    while Total < len(Twitter_ProfileLink):
        Remain = len(Twitter_ProfileLink) - Total
        print('\t\t\t  Loading:{} & Remaining:{}  '.format(Total + 1, Remain - 1))
        Response = requests.get(Twitter_ProfileLink[Total])
        if Response.status_code == 200:
            Soup = BeautifulSoup(Response.content, 'html.parser')
            # Finding Profile Header
            Header = Soup.find('p',{'class':'ProfileHeaderCard-bio'})
            if Header is not None:
                if fuzz.token_set_ratio(Header.text.lower(), Summary[Total].lower()) >= 50:
                    # Finding Image
                    Image = Soup.find('img', {'class': 'ProfileAvatar-image'})
                    if Image is not None:
                        Profile_Image.append(Image.get('src'))
                    else:
                        Profile_Image.append('N/A')
                        
                    ID = Soup.find('a', {'class': 'ProfileHeaderCard-screennameLink'})
                    if ID is not None:
                        print("Profile ID:{}".format(ID.text.replace('\n', '')))
                        Profile_ID.append(ID.text.replace('\n', ''))
                    else:
                       Profile_ID.append('N/A')
                    ProfileLink.append(Twitter_ProfileLink[Total])
                    Post = Soup.find('ol', {'id': 'stream-items-id'})
                    PostList = Post.find_all('li')
                    for P in PostList:
                        Block = P.find('div', {'class': 'js-stream-tweet'})
                        Latest_Post.append("https://twitter.com/" + Block.get('data-permalink-path'))
                        break
                    pass
                    Location = Soup.find('span', {'class': 'ProfileHeaderCard-locationText'})
                    if Location is not None:
                        Profile_Location.append(Location.text.replace('\n', ''))
                    name = Soup.find('a', {'class': 'ProfileHeaderCard-nameLink'})
                    if name is not None:
                        Profile_Username.append(name.text)
                        TwitterFollower(ID.text.replace('\n', ''))
                    else:
                        Profile_Username.append('N/A')
                else:
                    try:
                        Image = Soup.find('img', {'class': 'ProfileAvatar-image'})
                        if Image is not None:
                            Profile_Image.append(Image.get('src'))
                        else:
                            Profile_Image.append('N/A')
                        pass
                    except:
                        Profile_Image.append('N/A')
                    pass
                    try:
                        ID = Soup.find('a', {'class': 'ProfileHeaderCard-screennameLink'})
                        if ID is not None:
                            print("Profile ID:{}".format(ID.text.replace('\n', '')))
                            Profile_ID.append(ID.text.replace('\n', ''))
                        else:
                            Profile_ID.append('N/A')
                    except:
                        Profile_ID.append('N/A')
                    pass
                    ProfileLink.append(Twitter_ProfileLink[Total])
                    Post = Soup.find('ol', {'id': 'stream-items-id'})
                    PostList = Post.find_all('li')
                    for P in PostList:
                        Block = P.find('div', {'class': 'js-stream-tweet'})
                        Latest_Post.append("https://twitter.com/" + Block.get('data-permalink-path'))
                        break
                    pass
                    try:
                        Location = Soup.find('span', {'class': 'ProfileHeaderCard-locationText'})
                        if Location is not None:
                            Profile_Location.append(Location.text.replace('\n', ''))
                        else:
                            Profile_Location.append('N/A')
                        pass
                    except:
                        Profile_Location.append('N/A')
                    pass
                    try:
                        name = Soup.find('a', {'class': 'ProfileHeaderCard-nameLink'})
                        if name is not None:
                            Profile_Username.append(name.text)
                            TwitterFollowers,TwitterFriend=TwitterFollower(ID.text.replace('\n', ''))
                        else:
                            Profile_Username.append('N/A')
                        pass
                    except:
                        Profile_Username.append('N/A')
                    pass
                pass
        Total += 1
    pass
    print(type(TwitterFriend))
    return ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post,TwitterFollowers,TwitterFriend
    pass

# Extracting Twitter Profile Links from Google
def GoogleTwitter(FirstName,LastName,FullLocation,Summary):
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    Twitter_ProfileLink = []
    ProfileLink = []
    Profile_Username = []
    Profile_ID = []
    Profile_Location = []
    Profile_Image = []
    Latest_Post = []
    LinkedinSummary = []
    TwitterFollowers=[]
    TwitterFriend=[]
    Name = str(FirstName + " " + LastName)
    print('\t\t\t  Finding :{} Twitter Records  '.format(Name))
    Location = str(FullLocation.split(',')[0])
    Query = "{0} {1}".format(Name,Location)
    print(Query)
    response= requests.get("https://www.google.com/search?q=site:twitter.com " + str(Query), headers=header)
    Soup = BeautifulSoup(response.content, 'html.parser')
    if response.status_code == 200:
        Block = Soup.find_all('div', {'class': 'g'})
        for B in Block:
            Cite = B.find('cite')
            if Cite is not None:
                if Cite.text.__contains__("https://twitter.com/"):
                    try:
                        Link = B.find('div', {'class': 'r'}).find('h3')
                        if fuzz.token_set_ratio(Link.text.lower(), Name.lower()) >= 70:
                            Desc = B.find('span', {'class': 'st'})
                            if fuzz.token_set_ratio(Desc.text.lower(), Location.lower()) >= 70:
                                if not Cite.text.__contains__('status'):
                                    print(Cite.text)
                                    if not len(Twitter_ProfileLink)>0:
                                        Twitter_ProfileLink.append(Cite.text)
                                        LinkedinSummary.append(Summary)
                                    else:
                                        break
                                    pass
                                pass
                            pass
                        pass
                    except Exception as E:
                        print(E)
                    pass
                pass
            pass
        pass
    pass
    if len(Twitter_ProfileLink) > 0:       
        ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post,TwitterFollowers,TwitterFriend = GatherTwitterDetails(Twitter_ProfileLink,LinkedinSummary)
    return ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post ,TwitterFollowers,TwitterFriend
    pass  

# Extract Twitter Followers
def TwitterFollower(SearchPerson):
    SearchPerson=SearchPerson.replace('@','')
    print('Finding:{}'.format(SearchPerson))
    TwitterFollowers=[]
    TwitterFriend=[]
    consumer_key="8wrgzRIx0Sv1Jjzz2Lhp5kFCz"
    consumer_secret="wcDOywSkHCVQtkWxAJ4rOyiTnfaf8TYJtK7f07mmbDSVpWTWlQ"
    access_token="1070825270683136000-GljgIm6GhzliGWyLlCzcgzrEIBjxR8"
    access_token_secret="exAo5MJndYr0355UlOF6sQpMLRiKjvjFOwZtSDlEuvskM"
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=3, retry_delay=60)
        #user = api.get_user(SearchPerson)
        print('Getting Followers')
        try:
            for page in tweepy.Cursor(api.followers, screen_name=SearchPerson).items():
                if not len(TwitterFollowers)>50:
                    print(page.screen_name)
                    TwitterFollowers.append(page.screen_name)
                else:
                    break
                pass
            pass
        except:
            TwitterFollowers.append('N/A')
            print('Rate Limite Error')
        pass
        print('Getting Friends List')
        try:
            for page in tweepy.Cursor(api.friends, screen_name=SearchPerson).items():
                if not len(TwitterFriend)>30:
                    print(page.screen_name)
                    TwitterFriend.append(page.screen_name)
                else:
                    break
                pass
            pass
        except tweepy.TweepError:
            print('Rate Limite Error')
        pass
    except Exception as E:
        print(E)
    pass
    return TwitterFollowers,TwitterFriend
    pass

# Extracting Person ARTICLE/Post from Linkedin
def ExtractLinkedinPost(session,profileLink):
    print('\t\t\t  Finding LinkedIn Post  ')
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    #print(profileLink)
    Result = session.get(profileLink + '/detail/recent-activity/posts/', headers=header)
    Soup = BeautifulSoup(Result.content, 'html.parser')
    CodeIdGetter = Soup.findAll("code")
    CodeLen = len(CodeIdGetter)
    DataId = ""
    if len(CodeIdGetter) > 1:
        for C in CodeIdGetter:
            Id = str(C.get("id"))
            if not Id.__contains__("datalet"):
                if Id.__contains__("bpr-guid"):
                    Data = Soup.find("code", {"id": str(Id)})
                    if Data.text.__contains__("permaLink"):
                        DataId = Id
                    pass
                pass
            pass
        pass
    pass
    #print('Code Id:{}'.format(DataId))
    CodeData = Soup.findAll("code", {"id": str(DataId)})
    for C in CodeData:
        CodeData = C.text.encode('ascii','ignore')
    pass
    #print(CodeData)
    PostTitle = []
    PostLink = []
    JsonData = json.loads(CodeData)
    TotalLength = 0
    while TotalLength < JsonData['included'].__len__():
        try:
            if str(JsonData['included'][TotalLength]).__contains__("title"):
                P_Title = str(JsonData['included'][TotalLength]['title'])
                print(P_Title)
                PostTitle.append(P_Title)
            if str(JsonData['included'][TotalLength]).__contains__("permaLink"):
                P_Link = str(JsonData['included'][TotalLength]['permaLink'])
                PostLink.append(P_Link)
        except Exception as E:
            print(E) 
        pass
        TotalLength += 1
    pass
    return PostTitle,PostLink
    pass

# Extracting Person Group Information
def ExtractingGroupInfo(ProfileLink,Session):
    print('\t\t\t  Extracting Group Info of:{}'.format(ProfileLink+"/detail/interests/groups/"))
    GroupName=[]
    GroupLink=[]
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    Result = Session.get(ProfileLink+"/detail/interests/groups/", headers=header)
    Soup = BeautifulSoup(Result.content, 'html.parser')
    CodeIdGetter = Soup.findAll("code")
    CodeLen = len(CodeIdGetter)
    DataId = ""
    if len(CodeIdGetter) > 1:
        for C in CodeIdGetter:
            Id = str(C.get("id"))
            if not Id.__contains__("datalet"):
                if Id.__contains__("bpr-guid"):
                    Data = Soup.find("code", {"id": str(Id)})
                    if Data.text.__contains__('groupName'):
                        DataId = Id
                    pass
                pass
            pass
        pass
    pass
    CodeData = Soup.findAll("code", {"id": str(DataId)})
    for C in CodeData:
        CodeData = C.text
    pass
    JsonData = json.loads(CodeData)
    TotalLength = 0
    while TotalLength < JsonData['included'].__len__():
        try:
            if str(JsonData['included'][TotalLength]).__contains__("groupName"):
                Name = str(JsonData['included'][TotalLength]['groupName'])
                print(Name)
                GroupName.append(Name)
            if str(JsonData['included'][TotalLength]).__contains__("objectUrn"):
                Link = str(JsonData['included'][TotalLength]['objectUrn'])
                print("https://www.linkedin.com/groups/" + Link.replace('urn:li:group:', ''))
                GroupLink.append("https://www.linkedin.com/groups/" + Link.replace('urn:li:group:', ''))
        except:
            Group=False
        pass
        TotalLength += 1
    pass
    return GroupName,GroupLink
    pass

# Extracting Person Interest Information
def ExtractingInterestInfo(ProfileLink,session):
    print('\t\t\t  Exgtracting Interest Person:{}  '.format(ProfileLink+"/detail/interests/influencers/"))
    InterestName=[]
    InterestLink=[]
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0','From': 'qasimahsan77@gmail.com'}
    Result = session.get(ProfileLink+"/detail/interests/influencers/", headers=header)
    Soup = BeautifulSoup(Result.content, 'html.parser')
    CodeIdGetter = Soup.findAll("code")
    CodeLen = len(CodeIdGetter)
    DataId = []
    if len(CodeIdGetter) > 1:
        for C in CodeIdGetter:
            Id = str(C.get("id"))
            if not Id.__contains__("datalet"):
                if Id.__contains__("bpr-guid"):
                    Data = Soup.find("code", {"id": str(Id)})
                    #if Data.text.__contains__('occupation'):
                    if Data.text.__contains__('occupation'):
                        DataId.append(Id)
                    pass
                pass
            pass
        pass
    pass
    CodeData = Soup.findAll("code", {"id": str(DataId[0])})
    for C in CodeData:
        CodeData = C.text
    pass
    JsonData = json.loads(CodeData)
    TotalLength = 0
    while TotalLength < JsonData['included'].__len__():
        First=""
        if str(JsonData['included'][TotalLength]).__contains__("firstName"):
            First = str(JsonData['included'][TotalLength]['firstName'])
            print(First)
        if str(JsonData['included'][TotalLength]).__contains__("lastName"):
            Last = str(JsonData['included'][TotalLength]['lastName'])
            print(Last)
            InterestName.append(First+" "+Last)
        if str(JsonData['included'][TotalLength]).__contains__("publicIdentifier"):
            Link = str(JsonData['included'][TotalLength]['publicIdentifier'])
            print("https://www.linkedin.com/in/" + Link)
            InterestLink.append("https://www.linkedin.com/in/" + Link)
        TotalLength += 1
    pass
    return InterestName,InterestLink
    pass

def GeneratingPDF(FirstName, PostTitle,PostLink,GroupName,GroupLink,InterestName,InterestLink, CroppedImage,SkillsName):
    print('\t\t\t-----------------------')
    print('\t\t\t  Generating PDF File  ')
    print('\t\t\t-----------------------')
    CurrentDateTime = str(time.strftime("%c")).replace("/", "-")
    DateTime = CurrentDateTime.replace(":", "")
    try:
        Name = str(FirstName)+".jpg"
        r_img = requests.get(CroppedImage)
        f = open(str(FirstName)+".jpg", 'wb')
        f.write(r_img.content)
    except Exception as E:
        print(E)
        Name = '../../static/app/Images/Image_Not_Available.png'
    pass
    doc = SimpleDocTemplate("{0}{1}.pdf".format(str(FirstName), str(DateTime)), pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=18)
    Story = []
    try:
        im = Image("Logo.png", 2 * inch, 2 * inch, hAlign='CENTER')
        Story.append(im)
    except:
        print('\t\t\t  Unable to Add Images  ')
    pass

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT))

    ptext = '<font size=12>Finding the bonds that bring us closer</font>'
    Story.append(Paragraph(ptext, styles["Center"]))
    Story.append(Spacer(1, 12))

    try:
        im = Image(Name, 2 * inch, 2 * inch, hAlign='CENTER')
        Story.append(im)
    except:
        print('\t\t\t  Unable to Add Images  ')
    pass
    # Document/ PDF Style

    ptext = '<font size=12><b>Results for</b>:%s</font>' % (
        FirstName)
    Story.append(Paragraph(ptext, styles["Center"]))
    Story.append(Spacer(1, 12))
    # ------------------------------------
    # Now Displaying Linkedin Details.
    # ------------------------------------
    #Story.append(PageBreak())
    ptext = '<font size=12><b>Group Associations:</b></font>'
    Story.append(Paragraph(ptext, styles["Normal"]))
    Story.append(Spacer(1, 12))
    if len(GroupName) > 0:
        School = 0
        while School < len(GroupName):
            ptext='<link href="%s"><bullet>&bull;</bullet>%s</link>'%(GroupLink[School],GroupName[School])
            Story.append(Paragraph(ptext, styles["Bullet"]))
            Story.append(Spacer(1, 6))
            School += 1
        pass
    pass
    ptext = '<font size=14><b>How to help:</b></font>'
    Story.append(Paragraph(ptext, styles["Normal"]))
    Story.append(Spacer(1, 12))
    if len(SkillsName) > 0:
        Skill = 0
        while Skill < len(SkillsName):
            ptext='<bullet>&bull;</bullet>%s'%(SkillsName[Skill])
            Story.append(Paragraph(ptext, styles["Bullet"]))
            Story.append(Spacer(1, 6))
            Skill += 1
        pass
    pass
    ptext = '<font size=14><b>Recent Post</b></font>'
    Story.append(Paragraph(ptext, styles["Normal"]))
    Story.append(Spacer(1, 12))
    if len(PostTitle) > 0:
        Recommend = 0
        while Recommend < len(PostTitle):
            ptext='<link href="%s"><bullet>&bull;</bullet>%s</link>'%(PostLink[Recommend],PostTitle[Recommend])
            #ptext = '<link href="' + "PostLink[Recommend]" + '">''<bullet>&bull;</bullet>%s' % PostTitle[Recommend]
            Story.append(Paragraph(ptext, styles["Bullet"]))
            Story.append(Spacer(1, 6))
            Recommend += 1
        pass
    pass
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myFirstPage, canvasmaker=NumberedCanvas)
    print('\t\t\t  PDF File Saved Successfully  ')
    return str(FirstName) + str(DateTime)+".pdf"
    pass

def myFirstPage(canvas, doc):
    canvas.saveState()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Left', alignment=TA_LEFT))
    # Header
    #<img src="../../static/app/Images/Logo.png" height="50" width="50" valign="middle"/>
    header = Paragraph(
        ' Candidate Search Report',
        styles['Normal'])
    w, h = header.wrap(doc.width, doc.topMargin)
    header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
    # w, h = header.wrap(doc.width, doc.topMargin)
    # header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    # by <img src="VisibleFund_Logo.jpg" height="50" width="50" valign="middle"/>
    footer = Paragraph(
        'Prepared for Copyright  2018. All rights reserved',
        styles['Center'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)
    canvas.restoreState()
    pass

def myLaterPages(canvas, doc):
    canvas.saveState()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    #<img src="../../static/app/Images/Logo.png" height="50" width="50" valign="middle"/> by <img src="VisibleFund_Logo.jpg" height="50" width="50" valign="middle"/>
    footer = Paragraph(
        'Prepared for Copyright Charrypot 2018. All rights reserved',
        styles['Center'])
    w, h = footer.wrap(doc.width, doc.bottomMargin)
    footer.drawOn(canvas, doc.leftMargin, h)
    canvas.restoreState()
    pass

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """add page info to each page (page x of y)"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Change the position of this to wherever you want the page number to be
        self.drawRightString(195 * mm, 272 * mm,
                             "Page %d of %d" % (self._pageNumber, page_count))

    pass
    pass

def SendEmail(request):
    SentMessage=""
    if request.method=="GET" and request.is_ajax:
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login("charypotfriend@gmail.com", "IVYcrew1982")
            msg = MIMEMultipart()
            msg['From'] = "charypotfriend@gmail.com"
            msg['To'] = request.GET.get('pdfId').split("::")[1]
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = "Charypot saved your latest results. Check out!"
            text="Hey,\n\nJust in case you forgot some of the details from your search,don't worry.Here's the personalized PDF we created for you."
            msg.attach(MIMEText(text,'plain'))
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(request.GET.get('pdfId').split("::")[0], "rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename=' + str(request.GET.get('pdfId').split("::")[0]))
            msg.attach(part)
            server.sendmail("charypotfriend@gmail.com",request.GET.get('pdfId').split("::")[1], msg.as_string())
            print('\t\t\t  Email Send Successfully to:{}  '.format(request.GET.get('pdfId').split("::")[1]))
            server.quit()
            SentMessage="Email Send Successfully"
        except Exception as E:
            SentMessage=E
        pass
    pass
    return JsonResponse(SentMessage, safe=False)
    pass

def Demo(request):
    Approved = request.session.get('Approved')
    ProfileOne = request.session.get('ProfileOne')
    ProfileTwo = request.session.get('ProfileTwo')
    TwitterProfileOne = request.session.get('TwitterProfileOne')
    TwitterProfileTwo = request.session.get('TwitterProfileTwo')
    RecentPost = request.session.get('TwitterPost')
    LinkedInPost = request.session.get('LinkedInPost')
    L_GroupTwo = request.session.get('L_GroupTwo')
    L_InterestTwo = request.session.get('L_InterestTwo')
    InCommenData=request.session['InCommenData']
    PdfFileName=request.session['PdfFileName']
    return render(request,'app/Demo.html',
                  {'title':'Demo Page',
                   'year':datetime.now().year,
                   'Approved':Approved,
                   'ProfileOne':ProfileOne,
                   'ProfileTwo':ProfileTwo,
                   'TwitterProfileOne':TwitterProfileOne,
                   'TwitterProfileTwo':TwitterProfileTwo,
                   'TwitterPost':RecentPost,
                   'LinkedInPost':LinkedInPost,
                   'LinkedInGroup':L_GroupTwo,
                   'LinkedInInterest':L_InterestTwo,
                   'InCommenData':InCommenData,
                   'PdfFileName':PdfFileName
        })

def InCommonSection(ProfileOne,ProfileTwo,TwitterProfileOne,TwitterProfileTwo,L_GroupOne,L_GroupTwo,TwitterFolloweFriendOne,TwitterFolloweFriendTwo):
    FirstSkills=[]
    FirstSchool=[]
    TwoSkills=[]
    TwoSchool=[]
    # Matching List
    MatchSkills=[]
    MatchSchool=[]
    # First Person
    for FirstName, LastName, CurrentOccupation, ProfileURL, Headline, LocationName, IndustryName,Summary, Description, SchoolName, CompanyName, CroppedImage, ProfileOccupation, SkillsName,CompanyTitle,DegreeName,StudyField,Activity in ProfileOne:
        if len(SkillsName)>0:
            for Skill in SkillsName:
                FirstSkills.append(Skill.lower())
            pass
        else:
            FirstSkills.append('N/A')
        pass
        if len(SchoolName)>0:
            for School in SchoolName:
                FirstSchool.append(School.lower())
            pass
        else:
            FirstSchool.append('N/A')
        pass
    pass
    # Second Person
    print('Skills Section')
    try:
        for FirstName, LastName, CurrentOccupation, ProfileURL, Headline, LocationName, IndustryName,Summary, Description, SchoolName, CompanyName, CroppedImage, ProfileOccupation, SkillsName,CompanyTitle,DegreeName,StudyField,Activity in ProfileTwo:
            if len(SkillsName)>0:
                for Skill in SkillsName:
                    TwoSkills.append(Skill.lower())
                pass
            else:
                TwoSkills.append('N/A')
            pass
            if len(SchoolName)>0:
                for School in SchoolName:
                    TwoSchool.append(School.lower())
                pass
            else:
                TwoSchool.append('N/A')
            pass
        pass
        try:
            MatchSkills=list(set(FirstSkills).intersection(set(TwoSkills)))
        except:
            MatchSkills.append('N/A')
        pass
    except Exception as E:
        print(E)
    pass
    # /Now Finding the Similarities between Skills
    print('School Section')
    print(FirstSchool)
    print(TwoSchool)
    if len(FirstSchool)>1 and len(TwoSchool)>1:
        School=0
        while School<len(FirstSchool):
            try:
                if fuzz.token_set_ratio(FirstSchool[School].lower(), TwoSchool[School].lower()) >= 50:
                    MatchSchool.append(FirstSchool[School])
                elif fuzz.token_set_ratio(TwoSchool[School].lower(), FirstSchool[School].lower()) >= 50:
                    MatchSchool.append(TwoSchool[School])
                pass
            except Exception as E:
                print(E)
                MatchSchool.append('N/A')
                break
            pass
            School+=1
        pass
    else:
        MatchSchool.append('N/A')
    pass
    # Comparing Group By Their name
    print('Group Section')
    OneGName=[]
    TwoGName=[]
    if len(L_GroupOne)>1 and len(L_GroupTwo)>1:
        try:
            for name, link in L_GroupOne:
                OneGName.append(name)
            pass
        except Exception as E:
            print('Group One Error')
            print(E)
        pass
        try:
            for name, link in L_GroupTwo:
                TwoGName.append(name)
            pass
        except Exception as E:
            print('Group Two Error')
            print(E)
        pass
        # Now Comapring Both
        MatchGroupName=list(set(OneGName).intersection(set(TwoGName)))
    pass
    OneTwitterFollower=[]
    TwoTwitterFollower=[]
    OneTwitterFriend=[]
    TwoTwitterFriend=[]
    print('Person One Twitter')
    # Getting Twitter Followers and Friends
    try:
        for TwitterFollowers,TwitterFriend in TwitterFolloweFriendOne:
            OneTwitterFollower.append(TwitterFollowers)
            OneTwitterFriend.append(TwitterFriend)
        pass
    except Exception as E:
        print(E)
    pass
    print('Twitter Followere One')
    print(OneTwitterFollower)
    try:
        for TwitterFollowers,TwitterFriend in TwitterFolloweFriendTwo:
            TwoTwitterFollower.append(TwitterFollowers)
            TwoTwitterFriend.append(TwitterFriend)
        pass
    except Exception as E:
        print(E)
    pass
    print('Twitter Followere Two')
    print(TwoTwitterFollower)
    # Now Performing Exact matching
    MatchFollowers=list(set(OneTwitterFollower).intersection(set(TwoTwitterFollower)))
    MatchFriends=list(set(OneTwitterFriend).intersection(set(TwoTwitterFriend)))
    return MatchSkills,MatchSchool,MatchGroupName,MatchFollowers,MatchFriends
    pass
# Main Function which will control all the above functions

def finder(request):
    Approved=False
    Gat_FirstName = []
    Gat_LastName = [] 
    Gat_CurrentOccupation = []
    Gat_ProfileURL = []
    Gat_Headline = []
    Gat_LocationName = []
    Gat_IndustryName = []
    Gat_Summary = []
    Gat_Description = []
    Gat_SchoolName = []
    Gat_CompanyName = []
    Gat_CroppedImage = []
    Gat_ProfileOccupation = []
    Gat_SkillsName = []
    Gat_Title = []
    Gat_Degree = []
    Gat_StudyField = []
    Gat_Activity = []
    ProfileLink = []
    # Storing Linedin Result
    ProfileOne = []
    ProfileTwo = []
    # Twitter Fields
    TwitterProfileOne = []
    TwitterProfileTwo = []
    TwitterFolloweFriendOne=[]
    TwitterFolloweFriendTwo=[]
    # Twitter & Linkedin Post
    TwitterPost = []
    LinkedInPost = []
    # Linkedin Group & Interest Peoples
    L_GroupOne=[]
    L_InterestOne=[]
    L_GroupTwo=[]
    L_InterestTwo=[]
    # Interest Return Paramter
    InterestName=[]
    InterestLink=[]
    # Group Return Parameter
    GroupName=[]
    GroupLink=[]
    # Things which help in Machine Learning ALGO
    PersonOneSummary=""
    PersonTwoSummary=""
    # How To Help Skills,Latest Post Section
    HowToHelpSkills=[]
    RecentPost=[]
    InCommenData=""
    Approved = ""
    PdfFileName=""
    EmailAddress=""
    for key in list(request.session.keys()):
        print(request.session[key])
        del request.session[key]
    if request.method == "POST" or request.is_ajax():
        Approved = ""
        EmailAddress = request.POST.get('LinkedinEmail')
        Password = request.POST.get('LinkedinPassword')
        Skills = request.POST.get('Skills')
        NameList = request.POST.get('PersonTwo')
        TitleList = request.POST.get('TitleTwo')
        LocationList = request.POST.get('Compare_Location')
        form = ProfileForm(request.POST)
        if form.is_valid():
            LoginDone,Session,First,Last,Link,Occu = SignIn(EmailAddress,Password)
            if LoginDone:
                Person = 0
                while Person < 2:
                    # Saving Twitter Extracted Data
                    Profile_Username = []
                    Profile_ID = []
                    Profile_Location = []
                    Profile_Image = []
                    Latest_Post = []
                    TwitterFollowers=[]
                    TwitterFriend=[]
                    if Person == 0:
                        # Extracting Data From Basic Profiles of Person One
                        # Storing Owner Data into List
                        Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity = BasicProfile(NameList,TitleList,LocationList,Session,First,Last,Link,Occu,Person)
                        ProfileOne = zip(Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity)
                        ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post,TwitterFollowers,TwitterFriend = GoogleTwitter(Gat_FirstName[Person],Gat_LastName[Person],Gat_LocationName[Person],Gat_Summary[Person])
                        # Storing Owner Twitter Information
                        TwitterFolloweFriendOne=zip(TwitterFollowers,TwitterFriend)
                        TwitterProfileOne = zip(ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post)
                        # Getting Person One Interest & Group Information
                        GroupName,GroupLink=ExtractingGroupInfo(Gat_ProfileURL[Person],Session)
                        L_GroupOne=zip(GroupName,GroupLink)
                        # Interest Part
                        #L_InterestOne=zip(ExtractingInterestInfo(Gat_ProfileURL[Person],Session))
                    else:
                        # Now Extracting Comparison person Information
                        print('\t\t\t  Requesting Linkedin To Scrape Information  ')
                        Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity = BasicProfile(NameList,TitleList,LocationList,Session,First,Last,Link,Occu,Person)
                        for S in Gat_SkillsName:
                            HowToHelpSkills.append(S)
                        pass
                        ProfileTwo = zip(Gat_FirstName, Gat_LastName, Gat_CurrentOccupation, Gat_ProfileURL, Gat_Headline, Gat_LocationName, Gat_IndustryName,Gat_Summary, Gat_Description, Gat_SchoolName, Gat_CompanyName, Gat_CroppedImage, Gat_ProfileOccupation, Gat_SkillsName,Gat_Title,Gat_Degree,Gat_StudyField,Gat_Activity)
                    pass
                    Person+=1
                pass
                # Now Extracting Person Two Complete Information
                print('Total Name Length:{}'.format(len(Gat_FirstName)))
                Profile_Username = []
                Profile_ID = []
                Profile_Location = []
                Profile_Image = []
                Latest_Post = []
                TwitterFollowers=[]
                TwitterFriend=[]
                # Saving Linkedin Post Title & Link
                PostTitle = []
                PostLink = []
                Start = 0
                while Start < len(Gat_ProfileURL):
                    print('Extracting Compare Person Info')
                    ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post,TwitterFollowers,TwitterFriend = GoogleTwitter(Gat_FirstName[Start],Gat_LastName[Start],Gat_LocationName[Start],Gat_Summary[Start])
                    # Extracting Twitter Post/Other Information of Comparison
                    if len(Latest_Post)>0:
                        for P in Latest_Post:
                            RecentPost.append(P)
                        pass
                        RecentPost=Latest_Post
                    else:
                        RecentPost.append('Twitter Tweets not Find')
                    pass
                    TwitterFolloweFriendTwo=zip(TwitterFollowers,TwitterFriend)
                    TwitterProfileTwo = zip(ProfileLink,Profile_Username,Profile_ID,Profile_Location,Profile_Image,Latest_Post,TwitterFollowers,TwitterFriend)
                    # Extracting LinkeDin Post/Link
                    PostTitle,PostLink = ExtractLinkedinPost(Session,Gat_ProfileURL[Start])
                    # Zip Different List into One List
                    LinkedInPost = zip(PostTitle,PostLink)
                    # Extacting Linkedin Intrested Person Information
                    InterestName,InterestLink=ExtractingInterestInfo(Gat_ProfileURL[Start],Session)
                    L_InterestTwo=zip(InterestName,InterestLink)
                    # Extractng Linkedin Grouped Information
                    GroupName,GroupLink=ExtractingGroupInfo(Gat_ProfileURL[Start],Session)
                    L_GroupTwo=zip(GroupName,GroupLink)
                    PdfFileName=GeneratingPDF(Gat_FirstName[0],PostTitle,PostLink,GroupName,GroupLink,InterestName,InterestLink,Gat_CroppedImage[0],Gat_SkillsName[0])
                    # Extracting Twitter Post and Followers
                    Start+=1
                pass
                InCommenData=zip(InCommonSection(ProfileOne,ProfileTwo,TwitterProfileOne,TwitterProfileTwo,L_GroupOne,L_GroupTwo,TwitterFolloweFriendOne,TwitterFolloweFriendTwo))
            else:
                Approved = 'Login Credentials Not Valid Please try again'
            pass
        pass
    if request.method=="GET":
        return render(request,'app/finder.html',
                  {'title':'linkedin finder',
                   'year':datetime.now().year})
    if request.method=="POST":
        request.session['Approved'] = Approved
        request.session['ProfileOne'] = ProfileOne
        request.session['ProfileTwo'] = ProfileTwo
        request.session['TwitterProfileOne'] = TwitterProfileOne
        request.session['TwitterProfileTwo'] = TwitterProfileTwo
        request.session['TwitterPost'] = RecentPost
        request.session['LinkedInPost'] = LinkedInPost
        request.session['L_GroupTwo'] = L_GroupTwo
        request.session['L_InterestTwo'] = L_InterestTwo
        request.session['InCommenData']=InCommenData
        request.session['PdfFileName']=str(PdfFileName)+"::"+str(EmailAddress)
        return HttpResponseRedirect("Demo")
    pass

def RedirectDemo(request):
    print('into the Redirect Demo');
    return render(request,
        'app/RedirectDemo.html',
        {
            'title':'linkedin finder',
            'year':datetime.now().year,
        })

    pass

def LoginDemo(request):
    if request.method=="GET":
        print(request.method)
        return render(request,
        'app/LoginDemo.html',
        {
            'title':'linkedin finder',
            'year':datetime.now().year,
            'DeveloperName':'Muhammad Qasim'
        })
    elif request.method=="POST":
        print('Ajax Calling')
        return render(request,
        'app/RedirectDemo.html',
        {
            'title':'linkedin finder',
            'year':datetime.now().year,
            'DeveloperName':'Muhammad Qasim'
        })
        #return HttpResponseRedirect('RedirectDemo.html',{'DeveloperName':"Muhammad Qasim"})
    pass
