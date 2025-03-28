import streamlit as st, pandas as pd, os, requests, numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="MLB DW Data Refresh",
    layout="wide"
)

def dropUnnamed(df):
  df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
  return(df)

# Data Load
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, 'Files')
teamnamechangedf = pd.read_csv('{}/mlbteamnamechange.csv'.format(file_path))
teamnamechangedict = dict(zip(teamnamechangedf.Full, teamnamechangedf.Abbrev))
league_lev_df = pd.read_csv('{}/LeagueLevels.csv'.format(file_path))
levdict = dict(zip(league_lev_df.league_name,league_lev_df.level))
affdf = pd.read_csv('{}/Team_Affiliates.csv'.format(file_path))
affdict = dict(zip(affdf.team_id, affdf.parent_id))
affdict_abbrevs = dict(zip(affdf.team_id, affdf.parent_abbrev))
team_abbrev_look = dict(zip(affdf.team_name,affdf.team_abbrev))
idlookup_df = pd.read_csv('{}/IDLookupTable.csv'.format(file_path))
p_lookup_dict = dict(zip(idlookup_df.MLBID, idlookup_df.PLAYERNAME))
lsaclass = pd.read_csv('{}/lsaclass.csv'.format(file_path))
lsaclass = dropUnnamed(lsaclass)
lsaclass['launch_speed'] = round(lsaclass['launch_speed'],0)
lsaclass['launch_angle'] = round(lsaclass['launch_angle'],0)
lsaclass.columns=['launch_speed_round','launch_angle_round','launch_speed_angle']

try:
    current_data = pd.read_csv(f'{file_path}/MainFiles/allpbp2025.csv')
    current_dates = list(current_data['game_date'].unique())
    max_date = current_data['game_date'].max()
except:
   st.write('No data found, consider running a full-season refresh!')
   max_date = None
   current_data = pd.DataFrame()
try:
   current_hitboxes = pd.read_csv(f'{file_path}/MainFiles/allhitbox2025.csv')
except:
   current_hitboxes = pd.DataFrame()
try:
   current_pitchboxes = pd.read_csv(f'{file_path}/MainFiles/allpitchbox2025.csv')
except:
   current_pitchboxes = pd.DataFrame()

current_pitchboxes['Opp'] = np.where(current_pitchboxes['road_team']==current_pitchboxes['Team'],current_pitchboxes['home_team'],current_pitchboxes['road_team'])
current_pitchboxes['Park'] = current_pitchboxes['home_team']
current_pitchboxes['Date'] = current_pitchboxes['game_date']
# Sidebar menu
def sidebar_menu():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
            [
            "Data Refresh", 
            "Team Stats",
            "SP Report",
            "SP Profile"
            ]
    )
    return page

def getTodaysDate():
    from datetime import datetime
    import pytz
    eastern_timezone = pytz.timezone('US/Eastern')
    today_eastern = datetime.now(eastern_timezone)
    return today_eastern.strftime('%Y-%m-%d')

def getMLBSchedule():
  base_url = "https://statsapi.mlb.com/api/v1/schedule"
  params = {
      "sportId": 1,          # MLB
      "season": 2025,        # Year of the season
      "gameType": "R",       # Regular season games only
      "hydrate": "team"      # Include team details in the response
  }

  # Make the API request
  response = requests.get(base_url, params=params)

  # Check if the request was successful
  if response.status_code != 200:
      print(f"Error: Unable to fetch data (Status Code: {response.status_code})")
      exit()

  # Parse the JSON response
  data = response.json()

  # Extract game information
  games = []
  for date in data.get("dates", []):
      for game in date.get("games", []):
          game_info = {
              "Game ID": game["gamePk"],
              "Date": date["date"],
              "Time": game.get("gameDate", "").split("T")[1].split("Z")[0] if "gameDate" in game else "TBD",
              "Home Team": game["teams"]["home"]["team"]["name"],
              "Away Team": game["teams"]["away"]["team"]["name"],
              "Venue": game["venue"]["name"],
              "Status": game["status"]["detailedState"]
          }
          games.append(game_info)

  schedule_df = pd.DataFrame(games)
  schedule_df["Date"] = pd.to_datetime(schedule_df["Date"])
  schedule_df = schedule_df.sort_values(by="Date")
  schedule_df['Home Team'] = schedule_df['Home Team'].str.strip()
  schedule_df['Away Team'] = schedule_df['Away Team'].str.strip()
  schedule_df['Venue'] = schedule_df['Venue'].str.strip()

  schedule_df['Home Team'] = schedule_df['Home Team'].replace(teamnamechangedict)
  schedule_df['Away Team'] = schedule_df['Away Team'].replace(teamnamechangedict)

  my_schedule = pd.DataFrame()
  for team in schedule_df['Home Team'].unique():
    tsched = schedule_df[(schedule_df['Home Team']==team)|(schedule_df['Away Team']==team)]
    tsched['Team'] = team
    tsched['Opp'] = np.where(tsched['Home Team']==team,tsched['Away Team'],tsched['Home Team'])
    tsched['Date'] = pd.to_datetime(tsched['Date'])
    tsched = tsched[['Team','Opp','Date','Away Team','Home Team','Venue','Game ID','Status']]
    tsched = tsched.drop_duplicates(subset='Game ID')
    my_schedule = pd.concat([my_schedule,tsched])

  my_schedule = my_schedule.sort_values(by='Date')
  my_schedule = my_schedule.reset_index(drop=True)
  #my_schedule.to_csv('/content/drive/My Drive/FLB/Data/2025MLBSchedule.csv')
  return(my_schedule)

def getMLBSchedule2():
    base_url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {"sportId": 1,"season": 2025,"gameType": "R"}#,"hydrate": "team"}
   
    response = requests.get(base_url, params=params)
   
    data = response.json()
    games = []
    for date in data.get("dates", []):
            for game in date.get("games", []):
                game_info = {
                            "Game ID": game["gamePk"],
                            "Date": date["date"],
                            "Time": game.get("gameDate", "").split("T")[1].split("Z")[0] if "gameDate" in game else "TBD",
                            "Home Team": game["teams"]["home"]["team"]["name"],
                            "Away Team": game["teams"]["away"]["team"]["name"],
                            "Venue": game["venue"]["name"],
                            "Status": game["status"]["detailedState"]
                            }
            games.append(game_info)
    schedule_df = pd.DataFrame(games)
    st.write('1')
    st.write(schedule_df)
    
    schedule_df["Date"] = pd.to_datetime(schedule_df["Date"])
    schedule_df = schedule_df.sort_values(by="Date")
    schedule_df['Home Team'] = schedule_df['Home Team'].str.strip()
    schedule_df['Away Team'] = schedule_df['Away Team'].str.strip()
    schedule_df['Venue'] = schedule_df['Venue'].str.strip()

    schedule_df['Home Team'] = schedule_df['Home Team'].replace(teamnamechangedict)
    schedule_df['Away Team'] = schedule_df['Away Team'].replace(teamnamechangedict)
    
    my_schedule = pd.DataFrame()
    for team in schedule_df['Home Team'].unique():
        tsched = schedule_df[(schedule_df['Home Team']==team)|(schedule_df['Away Team']==team)]
        tsched['Team'] = team
        tsched['Opp'] = np.where(tsched['Home Team']==team,tsched['Away Team'],tsched['Home Team'])
        tsched['Date'] = pd.to_datetime(tsched['Date'])
        tsched = tsched[['Team','Opp','Date','Away Team','Home Team','Venue','Game ID','Status']]
        tsched = tsched.drop_duplicates(subset='Game ID')
        my_schedule = pd.concat([my_schedule,tsched])

    my_schedule = my_schedule.sort_values(by='Date')
    my_schedule.reset_index(drop=True)

    return(my_schedule)

def getRecentGames(schedule):
    import datetime
    today = pd.to_datetime(datetime.date.today())
    ten_days_ago = today - pd.DateOffset(days=10)
    last_ten_days = schedule[(pd.to_datetime(schedule['Date']).dt.date >= ten_days_ago.date())&(pd.to_datetime(schedule['Date']).dt.date <= today.date())]
    last_ten_days = last_ten_days.drop_duplicates(subset='Game ID')
    last_ten_days['Date'] = last_ten_days['Date'].dt.date
    return(last_ten_days)

def getGamePBP(game_pk, game_date, venue_name, league_id, game_type):
  url = 'https://statsapi.mlb.com/api/v1/game/{}/playByPlay'.format(game_pk)

  boxurl = 'https://statsapi.mlb.com/api/v1/game/{}/boxscore'.format(game_pk)
  box_game_info = requests.get(boxurl).json()
  lgname=box_game_info.get('teams').get('away').get('team').get('league').get('name')
  away_team = box_game_info.get('teams').get('away').get('team').get('name')
  away_team_id =  box_game_info.get('teams').get('away').get('team').get('id')
  home_team = box_game_info.get('teams').get('home').get('team').get('name')
  home_team_id = box_game_info.get('teams').get('home').get('team').get('id')

  game_info = requests.get(url).json()
  jsonstr = str(game_info)

  savtest='startSpeed' in jsonstr
  if savtest is True:
    statcastflag='Y'
  else:
    statcastflag='N'

  allplays = game_info.get('allPlays')

  gamepbp = pd.DataFrame()
  for play in allplays:
    currplay = play
    inningtopbot = currplay.get('about').get('halfInning')
    inning = currplay.get('about').get('inning')
    actionindex = currplay.get('actionIndex')
    at_bat_number = currplay.get('about').get('atBatIndex')+1
    currplay_type = currplay.get('result').get('type')
    currplay_res = currplay.get('result').get('eventType')
    currplay_descrip = currplay.get('result').get('description')
    currplay_rbi = currplay.get('result').get('rbi')
    currplay_awayscore = currplay.get('result').get('awayScore')
    currplay_homescore = currplay.get('result').get('homeScore')
    currplay_isout = currplay.get('result').get('isOut')
    playdata = currplay.get('playEvents')
    playmatchup = currplay.get('matchup')
    bid = playmatchup.get('batter').get('id')
    bname = playmatchup.get('batter').get('fullName')
    bstand = playmatchup.get('batSide').get('code')
    pid = playmatchup.get('pitcher').get('id')
    pname = playmatchup.get('pitcher').get('fullName')
    pthrows = playmatchup.get('pitchHand').get('code')

    for pitch in playdata:
      pdetails = pitch.get('details')
      checkadvise = pdetails.get('event')
      pitch_number = pitch.get('pitchNumber')
      if checkadvise is None:
        try:
          description = pdetails.get('call').get('description')
        except:
          description=None
        inplay = pdetails.get('isInPlay')
        isstrike = pdetails.get('isStrike')
        isball = pdetails.get('isBall')
        try:
          pitchname = pdetails.get('type').get('description')
          pitchtype = pdetails.get('type').get('code')
        except:
          pitchname=None
          pitchtype=None

        ballcount = pitch.get('count').get('balls')
        strikecount = pitch.get('count').get('strikes')
        try:
          plate_x = pitch.get('pitchData').get('coordinates').get('x')
          plate_y = pitch.get('pitchData').get('coordinates').get('y')
        except:
          plate_x = None
          plate_y = None

        try:
          startspeed = pitch.get('pitchData').get('startSpeed')
          endspeed = pitch.get('pitchData').get('endspeed')
        except:
          startspeed=None
          endspeed=None

        try:
          kzonetop = pitch.get('pitchData').get('strikeZoneTop')
          kzonebot = pitch.get('pitchData').get('strikeZoneBottom')
          kzonewidth = pitch.get('pitchData').get('strikeZoneWidth')
          kzonedepth = pitch.get('pitchData').get('strikeZoneDepth')
        except:
          kzonetop=None
          kzonebot=None
          kzonewidth=None
          kzonedepth=None


        try:
          ay = pitch.get('pitchData').get('coordinates').get('aY')
          ax = pitch.get('pitchData').get('coordinates').get('aX')
          pfxx = pitch.get('pitchData').get('coordinates').get('pfxX')
          pfxz = pitch.get('pitchData').get('coordinates').get('pfxZ')
          px = pitch.get('pitchData').get('coordinates').get('pX')
          pz = pitch.get('pitchData').get('coordinates').get('pZ')
          breakangle = pitch.get('pitchData').get('breaks').get('breakAngle')
          breaklength = pitch.get('pitchData').get('breaks').get('breakLength')
          break_y= pitch.get('pitchData').get('breaks').get('breakY')
          zone = pitch.get('pitchData').get('zone')
        except:
          ay=None
          ax=None
          pfxx=None
          pfxz=None
          px=None
          pz=None
          breakangle=None
          break_y=None
          breaklength=None
          zone=None

        try:
          hitdata = pitch.get('hitData')
          launchspeed = pitch.get('hitData').get('launchSpeed')
          launchspeed_round = round(launchspeed,0)
          launchangle = pitch.get('hitData').get('launchAngle')
          launchangle_round = round(launchangle,0)
          bb_type = pitch.get('hitData').get('trajectory')
          hardness = pitch.get('hitData').get('hardness')
          location = pitch.get('hitData').get('location')
          total_distance = pitch.get('hitData').get('totalDistance')
          coord_x = pitch.get('hitData').get('coordinates').get('coordX')
          coord_y = pitch.get('hitData').get('coordinates').get('coordY')

        except:
          #print('No hit data')
          launchspeed = None
          launchangle = None
          get_lsa = None
          bb_type = None
          hardness = None
          location = None
          coord_x = None
          coord_y = None

        #sav['BatterTeam'] = np.where(sav['inning_topbot']=='Top', sav['away_team'], sav['home_team'])
        # sav['PitcherTeam'] = np.where(sav['inning_topbot']=='Top', sav['home_team'], sav['away_team'])

        this_gamepbp = pd.DataFrame({'StatcastGame': statcastflag,
                                  'game_pk': game_pk, 'game_date': game_date, 'game_type': game_type, 'venue': venue_name,
                                  'league_id': league_id, 'league': lgname, 'level': levdict.get(lgname),
                                  'away_team': away_team,'away_team_id': away_team_id, 'away_team_aff': affdict.get(away_team),
                                  'home_team': home_team, 'home_team_id': home_team_id, 'home_team_aff': affdict.get(home_team),
                                  'player_name': pname, 'pitcher': pid, 'BatterName': bname, 'batter': bid,
                                  'stand': bstand, 'p_throws': pthrows,'inning_topbot': inningtopbot,
                                  'plate_x': plate_x, 'plate_y': plate_y,
                                  'inning': inning, 'at_bat_number':at_bat_number, 'pitch_number': pitch_number,
                                  'description': description, 'play_type': currplay_type, 'play_res':currplay_res,
                                  'play_desc': currplay_descrip,
                                  'rbi': currplay_rbi,'away_team_score':currplay_awayscore,
                                  'isOut': currplay_isout,'home_team_score':currplay_homescore,
                                  'isInPlay': inplay,'IsStrike':isstrike,'IsBall':isball,'pitch_name':pitchname,
                                  'pitch_type':pitchtype,'balls': ballcount,'strikes':strikecount,
                                  'release_speed':startspeed, 'end_pitch_speed': endspeed,'zone_top':kzonetop,
                                  'zone_bot':kzonebot,'zone_width':kzonewidth,'zone_depth':kzonedepth,'ay':ay,
                                  'ax':ax,'pfx_x':pfxx,'pfx_z':pfxz,'px':px,'pz':pz,'break_angle':breakangle,
                                  'break_length':breaklength,'break_y':break_y,'zone':zone,
                                  'launch_speed': launchspeed, 'launch_angle': launchangle,# 'hit_distance': total_distance,
                                  'bb_type':bb_type,'hit_location': location,'hit_coord_x': coord_x,
                                  'hit_coord_y': coord_y},index=[0])
        this_gamepbp['BatterTeam'] = np.where(this_gamepbp['inning_topbot']=='top', this_gamepbp['away_team'], this_gamepbp['home_team'])
        this_gamepbp['PitcherTeam'] = np.where(this_gamepbp['inning_topbot']=='top', this_gamepbp['home_team'], this_gamepbp['away_team'])
        this_gamepbp['PitchesThrown'] = 1
        gamepbp = pd.concat([gamepbp,this_gamepbp])

      else:
        #print('Found game advisory: {}'.format(checkadvise))
        pass
  gamepbp = gamepbp.reset_index(drop=True)
  gamepbp.to_csv(f'{file_path}/GameArchive/pbp/{game_pk}.csv')
  return(gamepbp)

def savAddOns(savdata):
  pdf = savdata.copy()

  pdf['away_team_aff_id'] = pdf['away_team_id'].map(affdict)
  pdf['away_team_aff'] = pdf['away_team_aff_id'].map(affdict_abbrevs)
  pdf['home_team_aff_id'] = pdf['home_team_id'].map(affdict)
  pdf['home_team_aff'] = pdf['home_team_aff_id'].map(affdict_abbrevs)

  pdf['IsWalk'] = np.where(pdf['balls']==4,1,0)
  pdf['IsStrikeout'] = np.where(pdf['strikes']==3,1,0)
  pdf['BallInPlay'] = np.where(pdf['isInPlay']==1,1,0)
  pdf['IsHBP'] = np.where(pdf['description']=='Hit By Pitch',1,0)
  pdf['PA_flag'] = np.where((pdf['balls']==4)|(pdf['strikes']==3)|(pdf['BallInPlay']==1)|(pdf['IsHBP']==1),1,0)


  pdf['IsHomer'] = np.where((pdf['play_res']=='home_run')&(pdf['PA_flag']==1),1,0)

  pitchthrownlist = ['In play, out(s)', 'Swinging Strike', 'Ball', 'Foul',
        'In play, no out', 'Called Strike', 'Foul Tip', 'In play, run(s)','Hit By Pitch',
        'Ball In Dirt','Pitchout', 'Swinging Strike (Blocked)',
        'Foul Bunt', 'Missed Bunt', 'Foul Pitchout',
        'Intent Ball', 'Swinging Pitchout']

  pdf['PitchesThrown'] = np.where(pdf['description'].isin(pitchthrownlist),1,0)

  map_pitchnames = {'Two-Seam Fastball': 'Sinker', 'Slow Curve': 'Curveball', 'Knuckle Curve': 'Curveball'}
  pdf['pitch_name'] = pdf['pitch_name'].replace(map_pitchnames)

  swstrlist = ['Swinging Strike','Foul Tip','Swinging Strike (Blocked)', 'Missed Bunt']
  cslist = ['Called Strike']
  cswlist = ['Swinging Strike','Foul Tip','Swinging Strike (Blocked)', 'Missed Bunt','Called Strike']
  contlist = ['Foul','In play, no out', 'In play, out(s)', 'Foul Pitchout','In play, run(s)']
  swinglist = ['Swinging Strike','Foul','In play, no out', 'In play, out(s)', 'In play, run(s)', 'Swinging Strike (Blocked)', 'Foul Pitchout']
  klist = ['strikeout', 'strikeout_double_play']
  bblist = ['walk','intent_walk']
  hitlist = ['single','double','triple','home_run']
  #balllist = ['Ball','Automatic Ball','Intent Ball','Pitchout']
  palist = ['strikeout','walk']

  isstrikelist = [ 'Swinging Strike', 'Foul','Called Strike', 'Foul Tip','Swinging Strike (Blocked)',
                  'Automatic Strike - Batter Pitch Timer Violation', 'Foul Bunt',
                  'Automatic Strike - Batter Timeout Violation', 'Missed Bunt',
                  'Automatic Strike','Foul Pitchout','Swinging Pitchout']

  isballlist = ['Ball', 'Hit By Pitch','Automatic Ball - Pitcher Pitch Timer Violation',
                'Ball In Dirt','Pitchout', 'Automatic Ball - Intentional', 'Automatic Ball',
                'Automatic Ball - Defensive Shift Violation','Automatic Ball - Catcher Pitch Timer Violation',
                'Intent Ball']

  pdf['IsStrike'] = np.where(pdf['description'].isin(isstrikelist),1,0)
  pdf['IsBall'] = np.where(pdf['description'].isin(isballlist),1,0)


  pdf['BatterTeam'] = np.where(pdf['inning_topbot']=='bottom', pdf['home_team'], pdf['away_team'])
  pdf['PitcherTeam'] = np.where(pdf['inning_topbot']=='bottom', pdf['away_team'], pdf['home_team'])

  pdf['BatterTeam_aff'] = np.where(pdf['inning_topbot']=='bottom', pdf['home_team_aff'], pdf['away_team_aff'])
  pdf['PitcherTeam_aff'] = np.where(pdf['inning_topbot']=='bottom', pdf['away_team_aff'], pdf['home_team_aff'])

  pdf['IsBIP'] = pdf['BallInPlay']

  pdf['PA'] = pdf['PA_flag']
  #pdf['AB'] = np.where((pdf['IsBIP']+pdf['IsStrikeout'])>0,1,0)
  pdf['IsHit'] = np.where((pdf['PA']==1)&(pdf['play_res'].isin(hitlist)),1,0)

  pdf['IsSwStr'] = np.where(pdf['description'].isin(swstrlist),1,0)
  pdf['IsCalledStr'] = np.where(pdf['description'].isin(cslist),1,0)
  pdf['ContactMade'] = np.where(pdf['description'].isin(contlist),1,0)
  pdf['SwungOn'] = np.where(pdf['description'].isin(swinglist),1,0)
  pdf['IsGB'] = np.where(pdf['bb_type']=='ground_ball',1,0)
  pdf['IsFB'] = np.where(pdf['bb_type']=='fly_ball',1,0)
  pdf['IsLD'] = np.where(pdf['bb_type']=='line_drive',1,0)
  pdf['IsPU'] = np.where(pdf['bb_type']=='popup',1,0)

  pdf['InZone'] = np.where(pdf['zone']<10,1,0)
  pdf['OutZone'] = np.where(pdf['zone']>9,1,0)
  pdf['IsChase'] = np.where(((pdf['SwungOn']==1)&(pdf['InZone']==0)),1,0)
  pdf['IsZoneSwing'] = np.where(((pdf['SwungOn']==1)&(pdf['InZone']==1)),1,0)
  pdf['IsZoneContact'] = np.where(((pdf['ContactMade']==1)&(pdf['InZone']==1)),1,0)

  pdf['IsSingle'] = np.where((pdf['play_res']=='single')&(pdf['PA_flag']==1),1,0)
  pdf['IsDouble'] = np.where((pdf['play_res']=='double')&(pdf['PA_flag']==1),1,0)
  pdf['IsTriple'] = np.where((pdf['play_res']=='triple')&(pdf['PA_flag']==1),1,0)

  ablist = ['field_out', 'double', 'strikeout', 'single','grounded_into_double_play',
            'home_run','fielders_choice', 'force_out', 'double_play', 'triple','field_error',
            'fielders_choice_out','strikeout_double_play','other_out', 'sac_fly_double_play','triple_play']

  pdf['AB'] = np.where((pdf['play_res'].isin(ablist))&(pdf['PA_flag']==1),1,0)

  try:
    pdf = pdf.drop(['launch_speed_angle'],axis=1)
  except:
    pass

  pdf['launch_angle'] = pdf['launch_angle'].replace([None], np.nan)
  pdf['launch_speed'] = pdf['launch_speed'].replace([None], np.nan)

  pdf['launch_angle_round'] = round(pdf['launch_angle'],0)
  pdf['launch_speed_round'] = round(pdf['launch_speed'],0)

  pdf = pd.merge(pdf, lsaclass, how='left', on=['launch_speed_round','launch_angle_round'])
  pdf['launch_speed_angle'] = np.where(pdf['launch_speed_round']<60,1,pdf['launch_speed_angle'])
  pdf['launch_speed_angle'] = np.where((pdf['launch_speed_angle'].isna())&(pdf['launch_speed']>1),1,pdf['launch_speed_angle'])

  pdf['IsBrl'] = np.where(pdf['launch_speed_angle']==6,1,0)
  pdf['IsSolid'] = np.where(pdf['launch_speed_angle']==5,1,0)
  pdf['IsFlare'] = np.where(pdf['launch_speed_angle']==4,1,0)
  pdf['IsUnder'] = np.where(pdf['launch_speed_angle']==3,1,0)
  pdf['IsTopped'] = np.where(pdf['launch_speed_angle']==2,1,0)
  pdf['IsWeak'] = np.where(pdf['launch_speed_angle']==1,1,0)
  ###

  ## zone stuff
  pdf['IsCalledStr'] = np.where(pdf['description']=='Called Strike',1,0)
  pdf['zone_bot2'] = pdf['zone_bot']*100
  pdf['zone_top2'] = pdf['zone_top']*100
  pdf['inzone_y'] = np.where((pdf['plate_y']>=pdf['zone_bot2'])&(pdf['plate_y']<=pdf['zone_top2']),1,0)
  pdf['inzone_x'] = np.where((pdf['plate_x']>=70)&(pdf['plate_x']<=140),1,0)
  pdf['InZone2'] = np.where((pdf['inzone_y']==1)&(pdf['inzone_x']==1),1,0)
  pdf['OutZone2'] = np.where(pdf['InZone2']==1,0,1)
  pdf['IsZoneSwing2'] = np.where((pdf['InZone2']==1)&(pdf['SwungOn']==1),1,0)
  pdf['IsChase2'] = np.where((pdf['OutZone2']==1)&(pdf['SwungOn']==1),1,0)
  pdf['IsZoneContact2'] = np.where((pdf['IsZoneSwing2']==1)&(pdf['ContactMade']==1),1,0)
  pdf['IsHardHit'] = np.where((pdf['IsBIP']==1)&(pdf['launch_speed']>=95),1,0)

  # HANDLE DUPLICATES
  dupes_hitter_df = pdf.groupby(['BatterName','batter'],as_index=False)['AB'].sum()
  hitter_dupes = dupes_hitter_df.groupby('BatterName',as_index=False)['batter'].count().sort_values(by='batter',ascending=False)
  hitter_dupes = hitter_dupes[hitter_dupes['batter']>1]
  hitter_dupes.columns=['Player','Count']
  hitter_dupes['Pos'] = 'Hitter'
  hitter_dupes_list = list(hitter_dupes['Player'])
  pdf['BatterName'] = np.where(pdf['BatterName'].isin(hitter_dupes_list),pdf['BatterName'] + ' - ' + pdf['batter'].astype(int).astype(str), pdf['BatterName'])

  dupes_pitcher_df = pdf.groupby(['player_name','pitcher'],as_index=False)['PitchesThrown'].sum()
  pitcher_dupes = dupes_pitcher_df.groupby('player_name',as_index=False)['pitcher'].count().sort_values(by='pitcher',ascending=False)
  pitcher_dupes = pitcher_dupes[pitcher_dupes['pitcher']>1]
  pitcher_dupes.columns=['Player','Count']
  pitcher_dupes['Pos'] = 'Pitcher'
  pitcher_dupes_list = list(pitcher_dupes['Player'])
  pdf['player_name'] = np.where(pdf['player_name'].isin(pitcher_dupes_list),pdf['player_name'] + ' - ' + pdf['pitcher'].astype(int).astype(str), pdf['player_name'])

  pdf = dropUnnamed(pdf)
  pdf['game_date'] = pd.to_datetime(pdf['game_date'])
  pdf['player_name'] = pdf['player_name'].replace({'Luis L. Ortiz': 'Luis Ortiz - 682847'})

  # drop dupes
  pdf = pdf.drop_duplicates(subset=['game_pk','pitcher','batter','inning','at_bat_number','pitch_number'])

  return(pdf)

def get_game_logs(game_date,game_pk):
    batting_logs = []
    pitching_logs = []
    url = (f'https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore')
    game_info = requests.get(url).json()
    for x in game_info.get('info'):
       labelcheck = x.get('label')
       if labelcheck =='Venue':
          venue = x.get('value')
          venue = venue[:-1]
    
    lgname=game_info.get('teams').get('away').get('team').get('league').get('name')
    if lgname == 'National League' or lgname == 'American League':
        lgname = 'MLB'

    away_team = game_info.get('teams').get('away').get('team').get('name')
    away_team = teamnamechangedict.get(away_team)
    away_team_id = game_info.get('teams').get('away').get('team').get('id')

    home_team = game_info.get('teams').get('home').get('team').get('name')
    home_team = teamnamechangedict.get(home_team)
    home_team_id = game_info.get('teams').get('home').get('team').get('id')

    if "teams" in game_info:
        for team in game_info["teams"].values():
            team_id = team.get('team').get('id')
            for player in team["players"].values():
                if player["stats"]["batting"]:
                    batting_log = {}
                    batting_log["game_date"] = game_date
                    batting_log["game_id"] = game_pk
                    batting_log["league_name"] = lgname
                    batting_log["level"] = lgname
                    batting_log["Team"] = teamnamechangedict.get(team.get('team').get('name'))
                    batting_log["team_id"] = team_id
                    batting_log["road_team"] = away_team
                    batting_log["home_team"] = home_team
                    batting_log["game_type"] = 'R'
                    batting_log["venue"] = venue
                    batting_log["Player"] = player["person"]["fullName"]
                    batting_log["player_id"] = int(player["person"]["id"])
                    batting_log["batting_order"] = player.get("battingOrder", "")
                    batting_log["AB"] = int(player["stats"]["batting"]["atBats"])
                    batting_log["R"] = int(player["stats"]["batting"]["runs"])
                    batting_log["H"] = int(player["stats"]["batting"]["hits"])
                    batting_log["2B"] = int(player["stats"]["batting"]["doubles"])
                    batting_log["3B"] = int(player["stats"]["batting"]["triples"])
                    batting_log["HR"] = int(player["stats"]["batting"]["homeRuns"])
                    batting_log["RBI"] = int(player["stats"]["batting"]["rbi"])
                    batting_log["SB"] = int(player["stats"]["batting"]["stolenBases"])
                    batting_log["CS"] = int(player["stats"]["batting"]["caughtStealing"])
                    batting_log["BB"] = int(player["stats"]["batting"]["baseOnBalls"])
                    batting_log["SO"] = int(player["stats"]["batting"]["strikeOuts"])
                    batting_log["IBB"] = int(player["stats"]["batting"]["intentionalWalks"])
                    batting_log["HBP"] = int(player["stats"]["batting"]["hitByPitch"])
                    batting_log["SH"] = int(player["stats"]["batting"]["sacBunts"])
                    batting_log["SF"] = int(player["stats"]["batting"]["sacFlies"])
                    batting_log["GIDP"] = int(player["stats"]["batting"]["groundIntoDoublePlay"])

                    batting_logs.append(batting_log)

                if player["stats"]["pitching"]:
                    pitching_log = {}
                    pitching_log["game_date"] = game_date
                    pitching_log["game_id"] = game_pk
                    pitching_log["league_name"] = lgname
                    pitching_log["level"] = lgname
                    pitching_log["Team"] = teamnamechangedict.get(team.get('team').get('name'))
                    pitching_log["team_id"] = team_id
                    pitching_log["road_team"] = away_team
                    pitching_log["road_team_id"] = away_team_id
                    pitching_log["home_team"] = home_team
                    pitching_log["home_team_id"] = home_team_id
                    pitching_log["game_type"] = "R"
                    pitching_log["venue_id"] = venue
                    pitching_log["league_id"] = lgname
                    pitching_log["Player"] = player["person"]["fullName"]
                    pitching_log["player_id"] = int(player["person"]["id"])
                    pitching_log["W"] = int(player["stats"]["pitching"].get("wins", ""))
                    pitching_log["L"] = int(player["stats"]["pitching"].get("losses", ""))
                    pitching_log["G"] = int(player["stats"]["pitching"].get("gamesPlayed", ""))
                    pitching_log["GS"] = int(player["stats"]["pitching"].get("gamesStarted", ""))
                    pitching_log["CG"] = int(player["stats"]["pitching"].get("completeGames", ""))
                    pitching_log["SHO"] = int(player["stats"]["pitching"].get("shutouts", ""))
                    pitching_log["SV"] = int(player["stats"]["pitching"].get("saves", ""))
                    pitching_log["HLD"] = int(player["stats"]["pitching"].get("holds", ""))
                    pitching_log["BFP"] = int(player["stats"]["pitching"].get("battersFaced", ""))
                    pitching_log["IP"] = float(player["stats"]["pitching"].get("inningsPitched", ""))
                    pitching_log["H"] = int(player["stats"]["pitching"].get("hits", ""))
                    pitching_log["ER"] = int(player["stats"]["pitching"].get("earnedRuns", ""))
                    pitching_log["R"] = int(player["stats"]["pitching"].get("runs", ""))
                    pitching_log["HR"] = int(player["stats"]["pitching"].get("homeRuns", ""))
                    pitching_log["SO"] = int(player["stats"]["pitching"].get("strikeOuts", ""))
                    pitching_log["BB"] = int(player["stats"]["pitching"].get("baseOnBalls", ""))
                    pitching_log["IBB"] = int(player["stats"]["pitching"].get("intentionalWalks", ""))
                    pitching_log["HBP"] = int(player["stats"]["pitching"].get("hitByPitch", ""))
                    pitching_log["WP"] = int(player["stats"]["pitching"].get("wildPitches", ""))
                    pitching_log["BK"] = int(player["stats"]["pitching"].get("balks", ""))

                    if pitching_log["GS"] > 0 and pitching_log["IP"] >= 6 and pitching_log["ER"] <= 3:
                        pitching_log["QS"] = 1
                    else:
                        pitching_log["QS"] = 0

                    pitching_logs.append(pitching_log)
    hitbox = batting_df = pd.DataFrame(batting_logs)
    pitchbox = pd.DataFrame(pitching_logs)

    hitbox.to_csv(f'{file_path}/GameArchive/box/hit/{game_pk}.csv')
    pitchbox.to_csv(f'{file_path}/GameArchive/box/pitch/{game_pk}.csv')
    return hitbox, pitchbox

def summarizeData(df):
   sum = df.groupby(['game_date','away_team','home_team'],as_index=False)[['away_team_score','home_team_score']].max()
   sum.columns=['Date','Road','Home','Road R','Home R']
   sum['Road'] = sum['Road'].replace(teamnamechangedict)
   sum['Home'] = sum['Home'].replace(teamnamechangedict)
   sum = sum.sort_values(by='Date',ascending=False)
   st.write('Pitches by Team by Date Summary:')
   st.dataframe(sum,hide_index=True)

def refreshData():
    todays_date = getTodaysDate()
    schedule = getMLBSchedule()
    #st.write(schedule)
    recent_games = getRecentGames(schedule)
    #st.write(recent_games)
    game_list = recent_games['Game ID'].unique()

    new_rows_pbp = pd.DataFrame()
    new_rows_hitbox = pd.DataFrame()
    new_rows_pitchbox = pd.DataFrame()
    for game in game_list:
       game_data=recent_games[recent_games['Game ID']==game]
       game_pk = game_data['Game ID'].iloc[0]
       game_date = game_data['Date'].iloc[0]
       venue_name = game_data['Venue'].iloc[0]
       league_id = 1
       game_type = 'R'
       game_pbp = getGamePBP(game_pk, game_date, venue_name, league_id, game_type)
       new_rows_pbp = pd.concat([new_rows_pbp,game_pbp])

       game_boxes = get_game_logs(game_date,game_pk)
       game_hit_box = game_boxes[0]
       new_rows_hitbox = pd.concat([new_rows_hitbox,game_hit_box])
       game_pitch_box = game_boxes[1]
       new_rows_pitchbox = pd.concat([new_rows_pitchbox,game_pitch_box])
    
    ## play by play update
    updated_data = pd.concat([current_data,new_rows_pbp])
    updated_data = updated_data.drop_duplicates(subset=['game_pk','at_bat_number','pitch_number','player_name','BatterName','balls','strikes'],keep='last')
    updated_data=savAddOns(updated_data)
    updated_data.to_csv(f'{file_path}/MainFiles/allpbp2025.csv')

    # hit box update
    updated_hitboxes = pd.concat([current_hitboxes,new_rows_hitbox])
    updated_hitboxes = dropUnnamed(updated_hitboxes)
    updated_hitboxes = updated_hitboxes.drop_duplicates(subset=['player_id','game_id'])
    updated_hitboxes.to_csv(f'{file_path}/MainFiles/allhitbox2025.csv')

    # pitch box update
    updated_pitchboxes = pd.concat([current_pitchboxes,new_rows_pitchbox])
    updated_pitchboxes = dropUnnamed(updated_pitchboxes)
    updated_pitchboxes = updated_pitchboxes.drop_duplicates(subset=['player_id','game_id'],keep='last')
    updated_pitchboxes.to_csv(f'{file_path}/MainFiles/allpitchbox2025.csv')

    st.write(f'Retrieved data for {len(game_list)} games')

    return(updated_data)

def runTeamStats():
    hit_basic_stats = current_hitboxes.groupby('Team',as_index=False)[['AB','SH','SF','BB','HBP','SB','HR','H','2B','3B','SO','R']].sum()
    hit_basic_stats['1B'] = hit_basic_stats['H']-hit_basic_stats['2B']-hit_basic_stats['3B']-hit_basic_stats['HR']
    hit_basic_stats['PA'] = hit_basic_stats['AB']+hit_basic_stats['SH']+hit_basic_stats['SF']+hit_basic_stats['BB']+hit_basic_stats['HBP']
    hit_basic_stats['AVG'] = round(hit_basic_stats['H']/hit_basic_stats['AB'],3)
    hit_basic_stats['OBP'] = round((hit_basic_stats['H']+hit_basic_stats['BB']+hit_basic_stats['HBP'])/hit_basic_stats['PA'],3)
    hit_basic_stats['SLG'] = round(((hit_basic_stats['1B'])+(hit_basic_stats['2B']*2)+(hit_basic_stats['3B']*3)+(hit_basic_stats['HR']*4))/hit_basic_stats['AB'],3)
    hit_basic_stats['OPS'] = hit_basic_stats['OBP'] + hit_basic_stats['SLG']
    hit_basic_stats['K%'] = round(hit_basic_stats['SO']/hit_basic_stats['PA'],3)
    hit_basic_stats['BB%'] = round(hit_basic_stats['BB']/hit_basic_stats['PA'],3)

    hit_basic_stats['wOBA'] = ((hit_basic_stats['BB']*.697)+(hit_basic_stats['HBP']*0.727)+(hit_basic_stats['1B']*0.855)+(hit_basic_stats['2B']*1.248)+(hit_basic_stats['3B']*1.575)+(hit_basic_stats['HR']*2.014))/(hit_basic_stats['AB']+hit_basic_stats['BB']+hit_basic_stats['SF']+hit_basic_stats['HBP'])

    hit_basic_stats = hit_basic_stats[['Team','PA','R','SB','HR','AVG','OBP','OPS','K%','BB%','wOBA']]

    hit_sav_stats = current_data.groupby('BatterTeam',as_index=False)[['PitchesThrown','InZone','IsZoneSwing','IsChase','OutZone','IsZoneContact','SwungOn','IsSwStr','IsBIP','IsGB','IsLD','IsFB','IsHardHit','IsBrl']].sum()
    hit_sav_stats['BatterTeam'] = hit_sav_stats['BatterTeam'].replace(teamnamechangedict)
    hit_sav_stats['SwStr%'] = round(hit_sav_stats['IsSwStr']/hit_sav_stats['PitchesThrown'],3)

    hit_sav_stats['O-Swing%'] = round(hit_sav_stats['IsChase']/hit_sav_stats['OutZone'],3)
    hit_sav_stats['Z-Contact%'] = round(hit_sav_stats['IsZoneContact']/hit_sav_stats['IsZoneSwing'],3)
    hit_sav_stats['GB%'] = round(hit_sav_stats['IsGB']/hit_sav_stats['IsBIP'],3)
    hit_sav_stats['LD%'] = round(hit_sav_stats['IsLD']/hit_sav_stats['IsBIP'],3)
    hit_sav_stats['FB%'] = round(hit_sav_stats['IsFB']/hit_sav_stats['IsBIP'],3)
    hit_sav_stats['Brl%'] = round(hit_sav_stats['IsBrl']/hit_sav_stats['IsBIP'],3)
    hit_sav_stats['HardHit%'] = round(hit_sav_stats['IsHardHit']/hit_sav_stats['IsBIP'],3)

    #xwoba_stat = current_data.groupby('BatterTeam',as_index=False)['estimated_woba_using_speedangle'].mean()
    #xwoba_stat.columns=['BatterTeam','xwOBA']
    #xwoba_stat['xwOBA'] = round(xwoba_stat['xwOBA'],3)
    #xwoba_con_stat = current_data[current_data['type']=='X'].groupby('BatterTeam',as_index=False)['estimated_woba_using_speedangle'].mean()
    #xwoba_con_stat.columns=['BatterTeam','xwOBACON']
    #xwoba_con_stat['xwOBACON'] = round(xwoba_con_stat['xwOBACON'],3)
    #hit_sav_stats = pd.merge(hit_sav_stats,xwoba_stat,left_on='BatterTeam',right_on='BatterTeam',how='left')
    #hit_sav_stats = pd.merge(hit_sav_stats,xwoba_con_stat,left_on='BatterTeam',right_on='BatterTeam',how='left')

    hit_sav_stats = hit_sav_stats[['BatterTeam','SwStr%','O-Swing%','Z-Contact%','GB%','LD%','FB%','HardHit%','Brl%']]#,'xwOBA','xwOBACON']]
    hit_sav_stats = hit_sav_stats.rename({'BatterTeam':'Team'},axis=1)


    all_final_stats = pd.merge(hit_basic_stats,hit_sav_stats,on='Team',how='left')

    all_final_stats = all_final_stats[['Team','PA','R','SB','HR','AVG','OBP','OPS','K%','BB%','SwStr%','O-Swing%','Z-Contact%','GB%','LD%','FB%','HardHit%','Brl%','wOBA']]#,'xwOBA','xwOBACON']]
    st.dataframe(all_final_stats,hide_index=True)

def plotPitchesNew(df):
    hitterhand = df['stand'].iloc[0]
    # Check for required columns
    required_cols = ['px', 'pz', 'pitch_type', 'zone_bot', 'zone_top']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col in df.columns]
        st.write(f"Error: Missing columns: {missing}")
        return None

    # Initialize figure with fixed size and DPI
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)  # Adjust figsize and dpi as needed

    # Get unique pitch types and create color mapping
    pitch_types = df['pitch_type'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(pitch_types)))
    color_dict = dict(zip(pitch_types, colors))

    # Scatter plot
    for pitch_type in pitch_types:
        pitch_data = df[df['pitch_type'] == pitch_type]
        ax.scatter(
            pitch_data['px'],
            pitch_data['pz'],
            c=[color_dict[pitch_type]],
            s=60,
            alpha=0.7,
            edgecolors='k',
            linewidth=0.5,
            label=pitch_type
        )

    # Strike zone
    strike_zone_left = -0.708
    strike_zone_right = 0.708
    strike_zone_bottom = df['zone_bot'].mean()
    strike_zone_top = df['zone_top'].mean()

    strike_zone = plt.Rectangle(
        (strike_zone_left, strike_zone_bottom),
        strike_zone_right - strike_zone_left,
        strike_zone_top - strike_zone_bottom,
        color='black',
        fill=False,
        linewidth=1.5,
        linestyle='--'
    )
    ax.add_patch(strike_zone)

    # Set plot limits
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(0, 5)

    # Customize plot
    ax.set_xlabel('Horizontal Location (feet)', fontsize=10)
    ax.set_ylabel('Vertical Location (feet)', fontsize=10)
    ax.set_title(f'Pitch Locations by Type vs. {hitterhand}HB', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legend
    ax.legend(
        title='Pitch Type',
        loc='upper right',
        fontsize=8,
        title_fontsize=10
    )

    plt.tight_layout()
    return fig

def plotPitchesNew2(df):
    hitterhand = df['stand'].iloc[0]
    # Check for required columns
    required_cols = ['px', 'pz', 'pitch_type', 'zone_bot', 'zone_top']
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        st.write(f"Error: Missing columns: {missing}")
        return None

    # Initialize figure
    fig, ax = plt.subplots(figsize=(6, 4))

    # Get unique pitch types and create color mapping
    pitch_types = df['pitch_type'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(pitch_types)))
    color_dict = dict(zip(pitch_types, colors))

    # Scatter plot using px and pz (in feet)
    for pitch_type in pitch_types:
        pitch_data = df[df['pitch_type'] == pitch_type]
        ax.scatter(
            pitch_data['px'],
            pitch_data['pz'],
            c=[color_dict[pitch_type]],
            s=60,
            alpha=0.7,
            edgecolors='k',
            linewidth=0.5,
            label=pitch_type
        )

    # Define strike zone in feet
    strike_zone_left = -0.708   # -17/2 inches = -0.708 feet
    strike_zone_right = 0.708   # +17/2 inches = 0.708 feet
    strike_zone_bottom = df['zone_bot'].mean()
    strike_zone_top = df['zone_top'].mean()

    # Draw strike zone rectangle
    strike_zone = plt.Rectangle(
        (strike_zone_left, strike_zone_bottom),
        strike_zone_right - strike_zone_left,
        strike_zone_top - strike_zone_bottom,
        color='black',
        fill=False,
        linewidth=1.5,
        linestyle='--'
    )
    ax.add_patch(strike_zone)

    # Set plot limits based on data (with some padding)
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(0, 5)

    # Customize plot
    ax.set_xlabel('Horizontal Location (feet)', fontsize=10)
    ax.set_ylabel('Vertical Location (feet)', fontsize=10)
    ax.set_title(f'Pitch Locations by Type vs. {hitterhand}HB', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Legend
    ax.legend(
        title='Pitch Type',
        loc='upper right',
        fontsize=8,
        title_fontsize=10
    )

    plt.tight_layout()
    return fig

def summarizeMixStats(df):
  sp_data = df.groupby(['player_name','PitcherTeam','pitch_type'],as_index=False)[['PitchesThrown','IsSwStr','IsBIP','IsGB','IsBrl','IsLD','IsFB','IsBall','IsStrike','IsStrikeout','IsWalk','PA_flag']].sum()
  sp_data = sp_data.rename({'player_name': 'Pitcher', 'PitcherTeam':'Team','pitch_type': 'Pitch'},axis=1)
  sp_data['Team'] = sp_data['Team'].replace(teamnamechangedict)
  sp_data['SwStr%'] = round(sp_data['IsSwStr']/sp_data['PitchesThrown'],3)
  sp_data['Strike%'] = round(sp_data['IsStrike']/sp_data['PitchesThrown'],3)
  sp_data['Ball%'] = round(sp_data['IsBall']/sp_data['PitchesThrown'],3)
  sp_data['K%'] = round(sp_data['IsStrikeout']/sp_data['PA_flag'],3)
  sp_data['BB%'] = round(sp_data['IsWalk']/sp_data['PA_flag'],3)
  sp_data['GB%'] = round(sp_data['IsGB']/sp_data['IsBIP'],3)
  sp_data['FB%'] = round(sp_data['IsFB']/sp_data['IsBIP'],3)
  sp_data['Brl%'] = round(sp_data['IsBrl']/sp_data['IsBIP'],3)
  sp_data = sp_data.sort_values(by='IsSwStr',ascending=False)

  velo = df.groupby(['player_name','PitcherTeam','pitch_type'],as_index=False)['release_speed'].mean()
  velo = velo.rename({'player_name': 'Pitcher', 'PitcherTeam':'Team','pitch_type': 'Pitch'},axis=1)
  sp_data = pd.merge(sp_data,velo,on=['Pitcher','Team','Pitch'],how='left')

  sp_data = sp_data[['Pitcher','Team','Pitch','PitchesThrown','PA_flag','IsStrikeout','IsWalk','K%','BB%','SwStr%','Strike%','Ball%','GB%','FB%','Brl%']]
  sp_data.columns=['Pitcher','Team','Pitch','PC','TBF','SO','BB','K%','BB%','SwStr%','Strike%','Ball%','GB%','FB%','Brl%']
  sp_data = sp_data.sort_values(by='PC',ascending=False)

  styled_df = sp_data.style.format({'SwStr%': '{:.1%}','Strike%': '{:.1%}','Ball%': '{:.1%}','K%': '{:.1%}',
                                    'BB%': '{:.1%}','GB%': '{:.1%}','FB%': '{:.1%}','Brl%': '{:.1%}',
                                    'PC': '{:.0f}','SO': '{:.0f}','BB': '{:.0f}','TBF': '{:.0f}'})
  return(styled_df)

def summarizePitcherStats(df):
  sp_data = df.groupby(['player_name','PitcherTeam'],as_index=False)[['PitchesThrown','IsSwStr','IsBIP','IsGB','IsBrl','IsLD','IsFB','IsBall','IsStrike','IsStrikeout','IsWalk','PA_flag']].sum()
  sp_data = sp_data.rename({'player_name': 'Pitcher', 'PitcherTeam':'Team'},axis=1)
  sp_data['Team'] = sp_data['Team'].replace(teamnamechangedict)
  sp_data['SwStr%'] = round(sp_data['IsSwStr']/sp_data['PitchesThrown'],3)
  sp_data['Strike%'] = round(sp_data['IsStrike']/sp_data['PitchesThrown'],3)
  sp_data['Ball%'] = round(sp_data['IsBall']/sp_data['PitchesThrown'],3)
  sp_data['K%'] = round(sp_data['IsStrikeout']/sp_data['PA_flag'],3)
  sp_data['BB%'] = round(sp_data['IsWalk']/sp_data['PA_flag'],3)
  sp_data['GB%'] = round(sp_data['IsGB']/sp_data['IsBIP'],3)
  sp_data['FB%'] = round(sp_data['IsFB']/sp_data['IsBIP'],3)
  sp_data['Brl%'] = round(sp_data['IsBrl']/sp_data['IsBIP'],3)
  sp_data = sp_data.sort_values(by='IsSwStr',ascending=False)
  sp_data = sp_data[['Pitcher','Team','PitchesThrown','PA_flag','IsStrikeout','IsWalk','K%','BB%','SwStr%','Strike%','Ball%','GB%','FB%','Brl%']]
  sp_data.columns=['Pitcher','Team','PC','TBF','SO','BB','K%','BB%','SwStr%','Strike%','Ball%','GB%','FB%','Brl%']

  styled_df = sp_data.style.format({'SwStr%': '{:.1%}','Strike%': '{:.1%}','Ball%': '{:.1%}','K%': '{:.1%}',
                                    'BB%': '{:.1%}','GB%': '{:.1%}','FB%': '{:.1%}','Brl%': '{:.1%}',
                                    'PC': '{:.0f}','SO': '{:.0f}','BB': '{:.0f}','TBF': '{:.0f}'})
  return(styled_df)

def get_player_image(player_id):
    return f'https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_426,q_auto:best/v1/people/{player_id}/headshot/67/current'

def pitcherProfile(current_data):
    current_data['game_date'] = pd.to_datetime(current_data['game_date'])
    
    # Layout for filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Player selection
    with col1:
        all_player_names = sorted(current_data['player_name'].unique())
        selected_player = st.selectbox(
            "Select Player",
            options=all_player_names,
            index=0,
            help="Search and select a player from the list"
        )
    
    # Date range selection
    with col2:
        min_date = st.date_input(
            "Start Date",
            value=current_data['game_date'].min().date(),
            min_value=current_data['game_date'].min().date(),
            max_value=current_data['game_date'].max().date(),
            format="YYYY-MM-DD",
            help="Select the start date for the range"
        )
    
    with col3:
        max_date = st.date_input(
            "End Date",
            value=current_data['game_date'].max().date(),
            min_value=current_data['game_date'].min().date(),
            max_value=current_data['game_date'].max().date(),
            format="YYYY-MM-DD",
            help="Select the end date for the range"
        )
    
    # Convert dates to datetime for comparison
    start_date = pd.to_datetime(min_date)
    end_date = pd.to_datetime(max_date)
    
    # Filter data
    mask = (current_data['game_date'] >= start_date) & (current_data['game_date'] <= end_date) & (current_data['player_name'] == selected_player)
    filtered_df = current_data.loc[mask].copy()

    st.markdown(f"<center><h2>{selected_player} from {min_date} - {max_date} ({len(filtered_df)} pitches)</h2></center>", unsafe_allow_html=True)
    
    # Display results
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(get_player_image(filtered_df['pitcher'].iloc[0]), width=185)
    with col2:
        statsdf = summarizePitcherStats(filtered_df)
        st.dataframe(statsdf, hide_index=True, width=900)
        mixdf = summarizeMixStats(filtered_df)
        st.dataframe(mixdf, hide_index=True)
    
    col1, col2 = st.columns([2,1.5])
    with col1:
      st.markdown(f"<h3>Game Logs</h3>", unsafe_allow_html=True)
      pbox = current_pitchboxes[current_pitchboxes['Player'] == selected_player][['Player','game_date','Opp','Park','G','GS','IP','H','ER','SO','BB','HR']]
      pbox = pbox.sort_values(by='game_date',ascending=False)
      #pbox.columns = ['Player','Date','Opp','Park','G','GS','IP','H','ER','SO','BB','HR']
      #st.dataframe(pbox)
      st.dataframe(pbox, width=750, hide_index=True)
    
    with col2:
      fig_vr = plotPitchesNew(filtered_df[filtered_df['stand']=='R'])
      st.pyplot(fig_vr, use_container_width=True)
      fig_vl = plotPitchesNew(filtered_df[filtered_df['stand']=='L'])
      st.pyplot(fig_vl, use_container_width=True)
        
def getSPReport():
    # Convert game_date to datetime and keep as datetime
    current_data['game_date'] = pd.to_datetime(current_data['game_date'])
    st.markdown(f"<h2><center>Filterable Pitcher Data</center></h3>", unsafe_allow_html=True)

    # Add date range picker
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=current_data['game_date'].min().date())
    with col2:
        end_date = st.date_input("End Date", value=current_data['game_date'].max().date())
    # Convert date picker inputs to datetime for comparison
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter data based on date range
    mask = (current_data['game_date'] >= start_date) & (current_data['game_date'] <= end_date)
    filtered_data = current_data.loc[mask]
    
    # Add team and pitcher filters
    col3, col4 = st.columns(2)
    
    # Team filter
    with col3:
        unique_teams = ['All Teams'] + sorted(filtered_data['PitcherTeam'].unique().tolist())
        # Replace team names in the selection list
        display_teams = [teamnamechangedict.get(team, team) for team in unique_teams]
        selected_team = st.selectbox("Select Team", display_teams)
        # Convert back to original team name if not 'All Teams'
        selected_team_original = unique_teams[display_teams.index(selected_team)] if selected_team != 'All Teams' else None
    
    # Pitcher filter
    with col4:
        if selected_team == 'All Teams':
            unique_pitchers = ['All Pitchers'] + sorted(filtered_data['player_name'].unique().tolist())
        else:
            unique_pitchers = ['All Pitchers'] + sorted(filtered_data[filtered_data['PitcherTeam'] == selected_team_original]['player_name'].unique().tolist())
        selected_pitcher = st.selectbox("Select Pitcher", unique_pitchers)
    st.markdown(f"<hr>", unsafe_allow_html=True)

    # Apply filters
    if selected_team != 'All Teams':
        filtered_data = filtered_data[filtered_data['PitcherTeam'] == selected_team_original]
    if selected_pitcher != 'All Pitchers':
        filtered_data = filtered_data[filtered_data['player_name'] == selected_pitcher]
    
    # Data processing with filtered data
    sp_data = filtered_data.groupby(['player_name','PitcherTeam'],as_index=False)[['PitchesThrown','IsBall','IsSwStr','IsStrike','PA_flag','IsHomer','IsStrikeout','IsWalk','IsBIP','IsGB']].sum()
    sp_data = sp_data.rename({'player_name': 'Pitcher', 'PitcherTeam':'Team'},axis=1)
    sp_data['Team'] = sp_data['Team'].replace(teamnamechangedict)
    sp_data['K%'] = round(sp_data['IsStrikeout']/sp_data['PA_flag'],3)
    sp_data['BB%'] = round(sp_data['IsWalk']/sp_data['PA_flag'],3)
    sp_data['SwStr%'] = round(sp_data['IsSwStr']/sp_data['PitchesThrown'],3)
    sp_data['Strike%'] = round(sp_data['IsStrike']/sp_data['PitchesThrown'],3)
    sp_data['Ball%'] = round(sp_data['IsBall']/sp_data['PitchesThrown'],3)
    sp_data['GB%'] = round(sp_data['IsGB']/sp_data['IsBIP'],3)

    sp_data = sp_data.rename({'PitchesThrown': 'PC', 'IsStrikeout': 'SO', 'PA_flag': 'TBF', 'IsWalk': 'BB','IsHomer': 'HR'},axis=1)
    sp_data = sp_data[['Pitcher','Team','PC','K%','BB%','SwStr%','Strike%','Ball%','GB%','HR']]
    
    sp_data = sp_data.sort_values(by='PC',ascending=False)
    styled_df = sp_data.style.format({'SwStr%': '{:.1%}','K%': '{:.1%}','BB%': '{:.1%}',
                                      'GB%': '{:.1%}','Strike%': '{:.1%}','Ball%': '{:.1%}'})
    st.dataframe(styled_df,hide_index=True,width=850,height=700)

def main():
    selected_page = sidebar_menu()
    st.markdown(f"<h1><center>MLB DW Data Tool</center></h1>", unsafe_allow_html=True)
    if selected_page == "Data Refresh":
        st.markdown(f'<h5><center><i><small>Data current as of {max_date} </small></i></center></h5>', unsafe_allow_html=True)

        if st.button("Refresh Data"):
           refreshData()
        
        if st.button("Summarize Data"):
           summarize_data = summarizeData(current_data)
    elif selected_page == 'Team Stats':
       runTeamStats()
    elif selected_page == 'SP Report':
       getSPReport()
    elif selected_page == 'SP Profile':
      pitcherProfile(current_data)   

if __name__ == "__main__":
    main()