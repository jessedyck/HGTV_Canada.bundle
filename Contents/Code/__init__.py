import re, datetime

NAME = "HGTV.ca"
ART = 'art-default.jpg'
ICON = 'icon-default.png'

HGTV_PARAMS = ["HmHUZlCuIXO_ymAAPiwCpTCNZ3iIF1EG", "z/HGTV%20Player%20-%20Video%20Center"]
FEED_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getCategoryList?PID=%s&startIndex=1&endIndex=500&query=hasReleases&query=CustomText|PlayerTag|%s&field=airdate&field=fullTitle&field=author&field=description&field=PID&field=thumbnailURL&field=title&contentCustomField=title&field=ID&field=parent"
FEEDS_LIST = "http://feeds.theplatform.com/ps/JSON/PortalService/2.2/getReleaseList?PID=%s&startIndex=1&endIndex=500&query=categoryIDs|%s&sortField=airdate&sortDescending=true&field=airdate&field=author&field=description&field=length&field=PID&field=thumbnailURL&field=title&contentCustomField=title"
DIRECT_FEED = "http://release.theplatform.com/content.select?format=SMIL&pid=%s&UserName=Unknown&Embedded=True&TrackBrowser=True&Tracking=True&TrackLocation=True"
#SHOW_CATS = ["Full Episodes","Sarah Richardson","Mike Holmes","Peter Fallico","Sam Pynn","Colin and Justin","Classics"]

####################################################################################################
def Start():

    Plugin.AddPrefixHandler("/video/hgtvcanada", MainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "InfoList"
    DirectoryItem.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
def MainMenu():

#     if not Platform.HasFlash:
#         return MessageContainer(NAME, L('This channel requires Flash. Please download and install Adobe Flash on the computer running Plex Media Server.'))

#	dir = LoadShowList(["Full Episodes","Sarah Richardson","Mike Holmes","Peter Fallico","Sam Pynn","Colin and Justin","Classics"])
	#dir = LoadShowList(["Sarah Richardson"])
#	return dir

	#dir = MediaContainer(viewGroup='List')
	#dir.Append(Function(DirectoryItem(LoadShowList, shows="Full Episodes"), category='fullepisodes'))
	dir.Append(Function(DirectoryItem(loadShowList, loadCats='["Full Episodes"]'), title='Full Episodes'))

	return dir
	
def Shows(showCat):
	dir = MediaContainer(viewGroup='List', title2=sender.itemTitle)
	

def LoadShowList(loadCats, title):
    dir = MediaContainer(viewGroup="List", title2=title)
    shows_with_seasons = {}
    shows_without_seasons = {}

    network = HGTV_PARAMS
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))

    #loadcats = ["%s",loadCats]
    loadCats = ["Full Episodes","Sarah Richardson","Mike Holmes","Peter Fallico","Sam Pynn","Colin and Justin","Classics"]


    for item in content['items']:
        if WantedCats(item['parent'],loadCats):
            title = item['title']
            id = item['ID']
            if re.search("Season", title):
                show, season = title.split("Season")
                show = show.rstrip().split(":")[0].rstrip().rstrip('.')
                if not(show in shows_with_seasons):
                    shows_with_seasons[show] = ""
                    dir.Append(Function(DirectoryItem(SeasonsPage, show), network=network))
            else:
                if not(title in shows_without_seasons):
                    shows_without_seasons[title] = []
                    shows_without_seasons[title].append(Function(DirectoryItem(VideosPage, title), pid=network[0], id=id))

    for show in shows_without_seasons:
        if not(show in shows_with_seasons) and len([added_show for added_show in shows_with_seasons if show in added_show or added_show in show]) == 0:
            for item in shows_without_seasons[show]:
                dir.Append(item)

    dir.Sort('title')

    return dir

####################################################################################################
def VideoPlayer(sender, pid):

    videosmil = HTTP.Request(DIRECT_FEED % pid).content
    player = videosmil.split("ref src")
    player = player[2].split('"')

    if ".mp4" in player[1]:
        player = player[1].replace(".mp4", "")
        try:
            clip = player.split(";")
            clip = "mp4:" + clip[4]
        except:
            clip = player.split("/video/")
            player = player.split("/video/")[0]
            clip = "mp4:/video/" + clip[-1]
    else:
        player = player[1].replace(".flv", "")
        try:
            clip = player.split(";")
            clip = clip[4]
        except:
            clip = player.split("/video/")
            player = player.split("/video/")[0]
            clip = "/video/" + clip[-1]

    return Redirect(RTMPVideoItem(player, clip))

####################################################################################################
def VideosPage(sender, pid, id):

    dir = MediaContainer(title2=sender.itemTitle, art=sender.art)
    pageUrl = FEEDS_LIST % (pid, id)
    feeds = JSON.ObjectFromURL(pageUrl)

    for item in feeds['items']:
        title = item['title']
        pid = item['PID']
        summary =  item['description'].replace('In Full:', '')
        duration = item['length']
        thumb = item['thumbnailURL']
        airdate = int(item['airdate'])/1000
        subtitle = 'Originally Aired: ' + datetime.datetime.fromtimestamp(airdate).strftime('%a %b %d, %Y')
        dir.Append(Function(VideoItem(VideoPlayer, title=title, subtitle=subtitle, summary=summary, thumb=thumb, duration=duration), pid=pid))

    return dir

####################################################################################################
def SeasonsPage(sender, network):

    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List", art=sender.art)
    content = JSON.ObjectFromURL(FEED_LIST % (network[0], network[1]))
    season_list = []

    for item in content['items']:
        if WantedCats(item['parent']) and sender.itemTitle in item['title']:
            title = item['title'].split(sender.itemTitle)[1].lstrip(':').lstrip('.').lstrip()
            if title not in season_list:
                season_list.append(title)
                id = item['ID']
                #thumb = item['thumbnailURL']
                dir.Append(Function(DirectoryItem(VideosPage, title, thumb=sender.thumb), pid=network[0], id=id))

    dir.Sort('title')

    return dir

####################################################################################################
def WantedCats(thisShow,loadCats):

    for show in loadCats:
        if show in thisShow:
            return 1                
    return 0
