#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import traceback
from typing import final
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import column
from forms import *
from flask_migrate import Migrate
from models import db, Artist, Venue, Show
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# SQLAlchemy dictionary converter"""


def dict_refiner(row): return {column.name: getattr(
    row, column.name) for column in row.__table__.columns}


# TODO connect to a local postgresql database
migrate = Migrate(app, db)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    # Get the list of venues to show to the user
    venue_groups = db.session.query(Venue.city, Venue.state).group_by(
        Venue.city, Venue.state).all()
    print(venue_groups)
    venues_data = []
    # Grouping venues by city and state
    for venue_group in venue_groups:
        city_name = venue_group[0]
        city_state = venue_group[1]
        query = db.session.query(Venue).filter(
            Venue.city == city_name, Venue.state == city_state)
        group = {
            "venues": [],
            "city": city_name,
            "state": city_state
        }
        venues = query.all()
        # List venues per city/state
        for venue in venues:
            print(venue.id)
            group['venues'].append({
                "id": venue.id,
                "name": venue.name,
                # TODO update data with upcoming shows per venue per city/state
                "num_upcoming_show": len(venue.shows) if hasattr(venue, 'shows') else 0
            })
        venues_data.append(group)
    return render_template('pages/venues.html', areas=venues_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    venues = db.session.query(Venue).filter((Venue.name.ilike('%{}%'.format(search_term))) |
                                            (Venue.city.ilike('%{}%'.format(search_term))) |
                                            (Venue.state.ilike('%{}%'.format(search_term)))).all()
    search_res = {
        "count": 0,
        "data": []
    }
    for venue in venues:
        v_obj = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": len(venue.shows) if hasattr(venue, 'shows') else 0
        }
        search_res["data"].append(v_obj)
    search_res['count'] = len(search_res['data'])
    return render_template('pages/search_venues.html', results=search_res, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = db.session.query(Venue).filter_by(id=venue_id).first()
    shows = Show.query.filter_by(venue_id=venue_id).all()

    if not venue:
        flash('Venue not found!', 'error')
        redirect('/venues')

    def upcoming_shows():
        upcoming = []

        for show in shows:
            if show.start_time > datetime.now():
                upcoming.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        return upcoming

    def past_shows():
        past = []

        for show in shows:
            if show.start_time < datetime.now():
                past.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        return past
    
    data = dict_refiner(venue)
    data["genres"] = data["genres"].split(';') if data['genres'] else []
    data["past_shows"] = past_shows()
    data["upcoming_shows"] = upcoming_shows()
    data['past_shows_count'] = len(past_shows())
    data['upcoming_shows_count'] = len(upcoming_shows())

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm()

    # on successful db insert, flash success
    try:
        data = request.form
        venue = Venue(
            name=data['name'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            genres=';'.join(data.getlist('genres')),
            website=data['website_link'],
            seeking_description=data['seeking_description'],
            #FIXME: Issue with dynamic data
            seeking_talent=True
        )

        db.session.add(venue)
        db.session.commit()

        print(data)

        flash('New venue ' +
              request.form['name'] +
              ' was successfully created!')

    # TODO: on unsuccessful db insert, flash an error instead.
    except:
        print(data)
        db.session.rollback()
        flash('An error occurred. New venue ' +
              request.form['name'] + ' could not be created.')
        traceback.print_exc()
        return render_template('forms/new_venue.html', form=form)
    finally:
        db.session.close()
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    try:
        venue_to_delete = Venue.query.filter(Venue.id == venue_id).one()
        venue_to_delete.delete()
        db.session.delete(venue)
        db.session.commit()

        flash("Venue {0} has been deleted successfully".format(
            venue_to_delete[0]['name']))
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be deleted.')
        traceback.print_exc()
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = db.session.query(Artist).all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get('search_term', '')
    artists = db.session.query(Artist).filter((Artist.name.ilike('%{}%'.format(search_term))) |
                                              (Artist.city.ilike('%{}%'.format(search_term))) |
                                              (Artist.state.ilike('%{}%'.format(search_term)))).all()
    response = {
        "count": 0,
        "data": []
    }
    for artist in artists:
        a_obj = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(artist.shows) if hasattr(artist, 'shows') else 0
        }
        response["data"].append(a_obj)
    response['count'] = len(response['data'])
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = db.session.query(Artist).filter_by(id=artist_id).first()
    shows = Show.query.filter_by(artist_id=artist_id).all()

    if not artist:
            flash('Artist not found!', 'error')
            return redirect('/artists')

    def upcoming_shows():
        upcoming = []

        for show in shows:
            if show.start_time > datetime.now():
                upcoming.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        return upcoming

    def past_shows():
        past = []

        for show in shows:
            if show.start_time < datetime.now():
                past.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
                    "start_time": format_datetime(str(show.start_time))

                })
        return past

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(';'),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        "website": artist.website,
        "past_shows": past_shows(),
        "upcoming_shows": upcoming_shows(),
        "past_shows_count": len(past_shows()),
        "upcoming_shows_count": len(upcoming_shows())
    }
    
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()
    if artist is None:
        flash('Artist not found!', 'error')
        return redirect('/artists')

    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = db.session.query(Artist).filter(
            Artist.id == artist_id).first()
        form_data = request.form
        artist.name = form_data['name']
        artist.city = form_data['city']
        artist.state = form_data['state']
        artist.phone = form_data['phone']
        artist.genres = ';'.join(form_data.getlist('genres'))
        artist.image_link = form_data['image_link']
        artist.facebook_link = form_data['facebook_link']
        artist.website = form_data['website_link']
        artist.seeking_venue = True
        artist.seeking_description = form_data['seeking_description']

        print(artist)
        # on successful db insert, flash success
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    # TODO on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')
        traceback.print_exc()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue = db.session.query(Venue).filter(
            Venue.id == venue_id).first()
        form_data = request.form
        venue.name = form_data['name']
        venue.city = form_data['city']
        venue.state = form_data['state']
        venue.phone = form_data['phone']
        venue.genres = ';'.join(form_data.getlist('genres'))
        venue.image_link = form_data['image_link']
        venue.facebook_link = form_data['facebook_link']
        venue.website = form_data['website_link']
        #FIXME: Issue with dynamic data
        venue.seeking_talent = True
        venue.seeking_description = form_data['seeking_description']

        print(venue)
        # on successful db insert, flash success
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
        traceback.print_exc()
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm()
    try:
        # on successful db insert, flash success
        data = request.form
        artist = Artist(
            name=data['name'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            genres=';'.join(data.getlist('genres')),
            website=data['website_link'],
            seeking_description=data['seeking_description'],
            #FIXME: Issue with dynamic data
            seeking_venue=True
        )

        db.session.add(artist)
        db.session.commit()

        print(data)

        flash('New artist ' +
              request.form['name'] + ' was successfully created!')
    except Exception as ex:
        # TODO on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        print(data)
        print(ex)
        db.session.rollback()
        flash('An error occurred. New artist ' +
              request.form['name'] + ' could not be created.')
        traceback.print_exc()
        return render_template('forms/new_artist.html', form=form)
    return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO replace with real venues data.
    shows = Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": str(show.start_time)
        })

    print(data)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm()
    try:
        # on successful db insert, flash success
        form_data = request.form
        artist = db.session.query(Artist).filter_by(
            id=form_data['artist_id']).first()
        # Check if artist to link exists
        if not artist:
            flash('Incorrect artist selected for the show!')
            return redirect('/shows/create')
        venue = db.session.query(Venue).filter_by(
            id=form_data['venue_id']).first()
        # Check if Venue to link to the show exist
        if not venue:
            flash('Incorrect venue selected for the show!')
            return redirect('/shows/create')

        show = Show(
            start_time=form_data['start_time'],
            artist_id=form_data['artist_id'],
            venue_id=form_data['venue_id']
        )

        db.session.add(show)
        db.session.commit()

        flash('New show starting ay ' +
              request.form['start_time'] +
              ' was successfully created!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        db.session.rollback()
        flash('An error occurred. New show ' +
              request.form['start_time'] + ' could not be created.')
        traceback.print_exc()
    finally:
        db.session.close()
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
