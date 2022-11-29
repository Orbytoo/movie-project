from flask import Flask, render_template, redirect, url_for, request
from flask_bs4 import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, Label
from wtforms.validators import DataRequired
import requests

# course 100 days of code 

MOVIE_DB_API_KEY = "    Your api key at 'https://www.themoviedb.org/'    "

SEARCH_URL_THE_MOVIE_DB = 'https://api.themoviedb.org/3/search/movie'
QUERY_DETAILS_URL_THE_MOVIE_DB = 'https://api.themoviedb.org/3/movie/'
MOVIE_DB_BASE_URL_ = 'https://image.tmdb.org/t/p/w500/'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# CREATE DB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(250), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=True)

    def __repr__(self):
        return f'title {self.title}'


class RateMovieForm(FlaskForm):
    rating =  FloatField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('You Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class FindMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    #This line creates a list of all the movies sorted by rating
    all_movies = db.session.query(Movie).order_by(Movie.rating).all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route('/edit', methods=['GET', 'POST'])
def rate_movie():
    form = RateMovieForm()

    movie_id = request.args.get('id', type=int)
    query_movie = Movie.query.get(movie_id)

    # Update label at runtime
    if query_movie.rating != None:
        form.rating.label = Label(form.rating.id, text=f'Your Rating Out of 10 e.g. 7.5  (Current Rating is {query_movie.rating})')

    if form.validate_on_submit():
        form_content = form.data
        
        db.session.query(Movie).filter(Movie.id == movie_id).\
            update({
                'rating': form_content.get('rating'),
                'review': form_content.get('review'),
            })
        db.session.commit()

        return redirect(url_for('home'))
    return render_template('edit.html', form=form, movie=query_movie, movie_title=query_movie.title)


@app.route('/delete', methods=['GET'])
def delete_movie():
    movie_id = request.args.get('id', type=int)
    
    db.session.query(Movie).filter(Movie.id == movie_id).\
        delete()
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = FindMovieForm()

    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(SEARCH_URL_THE_MOVIE_DB, params={'api_key': MOVIE_DB_API_KEY, 'query': movie_title})
        movie_list = response.json().get('results')

        return render_template('select.html', options=movie_list)

    return render_template('add.html', form=form)


@app.route('/get', methods=['GET'])
def find_movie():
    movie_api_id = request.args.get('id')

    if movie_api_id:
        movie_api_url = QUERY_DETAILS_URL_THE_MOVIE_DB + movie_api_id

        response = requests.get(movie_api_url, params={'api_key': MOVIE_DB_API_KEY, 'language': 'en-US'})
        data = response.json()

        new_movie = Movie(
            title =  data.get('title'),
            img_url = MOVIE_DB_BASE_URL_ + str(data.get('poster_path')), 
            year =  data.get('release_date').split('-')[0],
            description = data.get('overview'),  
        )
        db.session.add(new_movie)
        db.session.commit()

        movie_db = db.session.query(Movie).filter_by(title=new_movie.title).first()

        return redirect( url_for('rate_movie', id=movie_db.id) )


if __name__ == '__main__':
    app.run(debug=True)
