#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import os
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import ShowForm,VenueForm,ArtistForm
from sqlalchemy import func
import psycopg2

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

migrate = Migrate(app,db)

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean,nullable = True)
    talent_description = db.Column(db.String(500), nullable= True)
    venues = db.relationship('Show',backref= 'locate', lazy = True)

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue  = db.Column(db.Boolean, nullable = True)
    venue_description = db.Column(db.String(500),nullable = True)
    artists = db.relationship('Show',backref= 'perform', lazy=True)


class Show(db.Model):
  __tablename__ = "Show"
  id = db.Column(db.Integer,primary_key = True)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id'),nullable = False)
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id'),nullable = False)
  start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = Venue.query.distinct('city','state').all()
  def format_data(area):
    venues = Venue.query.filter_by(city=area.city,state=area.state).all()
    def format_venues(venue):
      # try to find shows from that venue
      shows = db.session.query(Show).filter(Show.venue_id == venue.id,func.date(Show.start_time)>=datetime.today())
      upcoming_shows = [show for show in shows]
      return {
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      }
    return {
      "city": area.city,
      "state": area.state,
      "venues": list(map(lambda venue: format_venues(venue=venue), venues))
    }
  data = list(map(lambda area: format_data(area=area), areas))
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_str = request.form.get('search_term')
  venue_query = db.session.query(Venue).filter(Venue.name.ilike('{}%'.format(search_str))).all()
  num_upcoming_shows = 0
  data = []
  if len(venue_query) < 0:
    response={
    "count": 0,
    "data": [{
      "id": '',
      "name": '',
      "num_upcoming_shows": ''
    }]
    }
  else:
    for venue in venue_query:
      venue_joined = db.session.query(Show).join(Venue, Venue.id == Show.venue_id).filter(Venue.id == venue.id).all()
      for musician in venue_joined:
        show_time = musician.start_time.strftime("%d-%b-%Y %H:%M:%S")
        today_time = datetime.today().strftime("%d-%b-%Y %H:%M:%S")
        if show_time > today_time:
          num_upcoming_shows +=1
      data.append({"id":venue.id,"name": venue.name, "num_upcoming_shows":num_upcoming_shows})
    response = {"count":len(venue_query),"data":data} 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue= db.session.query(Venue).filter_by(id = venue_id).first()
  shows = db.session.query(Show).filter_by(venue_id = venue_id).all()

  venue_obj = {'id':venue.id,'name' : venue.name,'city': venue.city,'state':venue.state,'website':venue.website,
  'phone': venue.phone,'facebook_link':venue.facebook_link,'image_link':venue.image_link,
  'seeking_talent': venue.seeking_talent,'address':venue.address,'seeking_description':venue.talent_description}

  past_shows = []
  past_shows_count = 0
  upcoming_shows = []
  upcoming_shows_count = 0

  for show in shows:
    artist_in_show = {'artist_id':show.artist_id,'start_time':show.start_time}
    artist_data = db.session.query(Artist).join(Show,Show.artist_id == Artist.id).filter(Artist.id == artist_in_show['artist_id']).all()
    for artist in artist_data:
      show_time = artist_in_show['start_time'].strftime("%d-%b-%Y %H:%M:%S")
      today_time = datetime.today().strftime("%d-%b-%Y %H:%M:%S")
      
      if show_time < today_time:
        past = {'artist_id':artist.id,'name':artist.name,'artist_image_link':artist.image_link,
        'start_time': show.start_time}
        past_shows.append(past)
        past_shows_count += 1
      else:
        upcoming = {'artist_id':artist.id,'name':artist.name,'artist_image_link':artist.image_link,
        'start_time': show.start_time}
        upcoming_shows.append(upcoming)
        upcoming_shows_count +=1

  venue_obj['past_shows'] = past_shows
  venue_obj['past_shows_count'] = past_shows_count
  venue_obj['upcoming_shows'] = upcoming_shows
  venue_obj['upcoming_shows_count'] = upcoming_shows_count

  return render_template('pages/show_venue.html', venue=venue_obj)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(request.form)
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    seeking_talent = False
    talent_description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = True
    if 'seeking_description' in request.form:
      talent_description = request.form['seeking_description']
    venue = Venue(name=request.form['name'],city=request.form['city'],state=request.form['state'],
    phone=request.form['phone'],website=request.form['website'],image_link=request.form['image_link']
    ,facebook_link=request.form['facebook_link'],seeking_talent=seeking_talent,
    talent_description=talent_description)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist_query = db.session.query(Artist).all()
  data = []
  for artist in artist_query:
    data_obj = {'id':artist.id,'name': artist.name}
    data.append(data_obj)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_str = request.form.get('search_term')
  artist_query = db.session.query(Artist).filter(Artist.name.ilike('{}%'.format(search_str))).all()
  num_upcoming_shows = 0
  data = []
  if len(artist_query) < 0:
    response={
    "count": 0,
    "data": [{
      "id": '',
      "name": '',
      "num_upcoming_shows": ''
    }]
    }
  else:
    for artist in artist_query:
      artist_joined = db.session.query(Show).join(Artist, Artist.id == Show.artist_id).filter(Artist.id == artist.id).all()
      for musician in artist_joined:
        show_time = musician.start_time.strftime("%d-%b-%Y %H:%M:%S")
        today_time = datetime.today().strftime("%d-%b-%Y %H:%M:%S")
        if show_time > today_time:
          num_upcoming_shows +=1
      data.append({"id":artist.id,"name": artist.name, "num_upcoming_shows":num_upcoming_shows})
    response = {"count":len(artist_query),"data":data}  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))
  

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist= db.session.query(Artist).filter_by(id = artist_id).first()
  shows = db.session.query(Show).filter_by(artist_id= artist_id).all()

  artist_obj = {'id':artist.id,'name' : artist.name,'city': artist.city,'state':artist.state,'website':artist.website,
  'phone': artist.phone,'genres':artist.genres,'facebook_link':artist.facebook_link,
  'image_link':artist.image_link, 'seeking_venue': artist.seeking_venue,'seeking_venue':artist.seeking_venue}

  past_shows = []
  past_shows_count = 0
  upcoming_shows = []
  upcoming_shows_count = 0

  for show in shows:
    venue_in_show = {'venue_id':show.venue_id,'start_time':show.start_time}
    venue_data = db.session.query(Venue).join(Show,Show.venue_id == Venue.id).filter(Venue.id == venue_in_show['venue_id']).all()
    
    for venue in venue_data:
      show_time = venue_in_show['start_time'].strftime("%d-%b-%Y %H:%M:%S")
      today_time = datetime.today().strftime("%d-%b-%Y %H:%M:%S")
      if show_time< today_time:
        past = {'venue_id':venue.id,'name':venue.name,'venue_image_link':venue.image_link,
        'start_time': show.start_time}
        past_shows.append(past)
        past_shows_count += 1
      else:
        upcoming = {'venue_id':venue.id,'name':venue.name,'venue_image_link':venue.image_link,
        'start_time': show.start_time}
        upcoming_shows.append(upcoming)
        upcoming_shows_count +=1
  artist_obj['past_shows'] = past_shows
  artist_obj['past_shows_count'] = past_shows_count
  artist_obj['upcoming_shows'] = upcoming_shows
  artist_obj['upcoming_shows_count'] = upcoming_shows_count
  return render_template('pages/show_artist.html', artist=artist_obj)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id = artist_id).one()
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    if request.form['seeking_venue'] == 'y':
      seeking_venue = True
      seeking_description = request.form['seeking_description']
    else:
      seeking_venue = False
      seeking_description = None
    new_artist = dict(name=request.form['name'],city = request.form['city'],
    state= request.form['state'],address = request.form['address'], genres = request.form['genres'],
    facebook_link = request.form['facebook_link'],image_link=request.form['image_link'],
    website = request.form['website'], seeking_venue= seeking_venue,
    seeking_description = seeking_description)
    db.session.query(Artist).filter(Artist.id==artist_id).update(new_artist)
    db.session.commit()
    flash('Artist was edited to be ' + request.form['name'] + ' succesfully.')

  except Exception as e:
    print(e)
    flash('Artist was not edited succesfully.')
    db.session.rollback()
  finally:
    db.session.close() 
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter_by(id = venue_id).one()
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    if request.form['seeking_talent'] == 'y':
      seeking_talent = True
      talent_description = request.form['seeking_description']
    else:
      seeking_talent = False
      talent_description = None

    new_venue = dict(name=request.form['name'],city = request.form['city'],
    state= request.form['state'],address = request.form['address'],
    facebook_link = request.form['facebook_link'],image_link=request.form['image_link'],
    website = request.form['website'], seeking_talent = seeking_talent,
    talent_description = talent_description)
    db.session.query(Venue).filter(Venue.id==venue_id).update(new_venue)
    db.session.commit()
    flash('Venue was edited to be ' + request.form['name'] + ' succesfully.')

  except Exception as e:
    print(e)
    flash('Venue was not edited succesfully.')
    db.session.rollback()
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(request.form)
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  data = {}
  try:
    seeking_venue = False
    venue_description = ''
    
    if 'seeking_venue' in request.form:
      seeking_venue = True
    if 'venue_description' in request.form:
      venue_description = request.form['venue_description']
    
    artist = Artist(name=request.form['name'],genres=request.form['genres'],
    city=request.form['city'],state=request.form['state'],phone=request.form['phone'],website=request.form['website'],
    facebook_link=request.form['facebook_link'],seeking_venue=seeking_venue,
    venue_description=venue_description,image_link=request.form['image_link'])
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except Exception as e:
    error = True
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  finally:
    db.session.close()
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
      data.append({
          "venue_id": show.venue_id,
          "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
          "artist_id": show.artist_id,
          "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
          "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
          "start_time": show.start_time.strftime("%d-%b-%Y %H:%M:%S")
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm(request.form)
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show(artist_id = request.form['artist_id'],venue_id=request.form['venue_id'],
    start_time = request.form['start_time'] )
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')

  except Exception as e:
    print(e)
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
""" if __name__ == '__main__':
    app.run() """

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

