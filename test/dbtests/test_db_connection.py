from pgsqlutils.base import syncdb
from pgsqlutils.orm import Session, BaseModel
from pgsqlutils.exceptions import NotFoundError

from .models import Artist, Album, Genre, User

import pytest


class TestDB(object):
    def test_connection_open(self):
        """
        checks if connection is open
        """
        result = Session.execute('SELECT 19;')
        assert result.fetchone()[0] == 19
        Session.close()


class TestCaseModel(object):
    def setup(self):
        syncdb()

    def test_simple_insert(self):
        assert 0 == Artist.objects.count()
        artist = Artist()
        artist.add()
        assert 1 == Artist.objects.count()
        artist2 = Artist()
        artist2.add()
        assert 2 == Artist.objects.count()

    def test_multi_insert(self):
        assert 0 == Genre.objects.count()
        data = [
            Genre(
                name='genre{}'.format(x), description='descript{}'.format(x))
            for x in range(100)
        ]

        Genre.objects.add_all(data)
        Session.commit()
        assert 100 == Genre.objects.count()

    def test_relationships(self):
        rock = Genre(name='Rock', description='rock yeah!!!')
        rock.add()
        pink = Artist(
            genre_id=rock.id, name='Pink Floyd', description='Awsome')
        pink.add()
        dark = Album(
            artist_id=pink.id, name='Dark side of the moon',
            description='Interesting')
        dark.add()

        rolling = Artist(
            genre_id=rock.id, name='Rolling Stones', description='Acceptable')

        rolling.add()

        hits = Album(
            artist_id=rolling.id, name='Greatest hits',
            description='Interesting')
        hits.add()

        assert 2 == Album.objects.count()

        wall = Album(
            artist_id=pink.id, name='The Wall',
            description='Interesting')
        wall.add()
        assert 2 == len(pink.albums)
        assert 2 == len(Artist.objects.filter_by(genre_id=rock.id)[:])

    def test_update(self):
        rock = Genre(name='Rock', description='rock yeah!!!')
        rock.add()
        description_updated = 'description_updated'
        rock.description = description_updated
        rock.update()
        rock2 = Genre.objects.get(id=rock.id)
        assert rock2.description == description_updated
        assert 1 == Genre.objects.count()

    def test_get_for_update(self):
        rock = Genre(name='Rock', description='rock yeah!!!')
        rock.add()
        rock2 = Genre.objects.get_for_update(id=rock.id)
        assert rock2.id == rock.id

    def test_delete(self):
        rock = Genre(name='Rock', description='rock yeah!!!')
        rock.add()
        assert 1 == Genre.objects.count()
        rock.delete()
        assert 0 == Genre.objects.count()

    def test_raw_sql(self):
        rock = Genre(name='Rock', description='rock yeah!!!')
        rock.add()
        pink = Artist(
            genre_id=rock.id, name='Pink Floyd', description='Awsome')
        pink.add()
        dark = Album(
            artist_id=pink.id, name='Dark side of the moon',
            description='Interesting')
        dark.add()
        rolling = Artist(
            genre_id=rock.id, name='Rolling Stones', description='Acceptable')

        rolling.add()

        sql = """
            SELECT a.name as artist_name, a.description artist_description,
            g.name as artist_genre
            FROM artist a
            INNER JOIN genre g ON a.genre_id = g.id
            ORDER BY a.id DESC;
        """

        result = Genre.objects.raw_sql(sql).fetchall()
        assert 2 == len(result)
        assert 'Rolling Stones' == result[0][0]

        sql = """
            SELECT a.name as artist_name, a.description artist_description,
            g.name as artist_genre
            FROM artist a
            INNER JOIN genre g ON a.genre_id = g.id
            WHERE a.id = :artist_id
            ORDER BY a.id DESC;
        """

        result = Genre.objects.raw_sql(sql, artist_id=pink.id).fetchall()
        assert 1 == len(result)
        assert 'Pink Floyd' == result[0][0]

    def test_not_found(self):
        with pytest.raises(NotFoundError) as excinfo:
            Genre.objects.get(id=-666)
        assert "Object not found" in str(excinfo.value)

    def test_encrypted_password(self):
        user = User(username='username', email='eil@il.com', password='123')
        user.add()
        id = user.id
        # objects needs to dereferenciated otherwise
        # user2 will be just a copy of user
        user = None
        user2 = User.objects.get(id=id)
        assert id == user2.id
        assert '123' == user2.password

    def test_get_insert(self):
        """
        Testing password field
        """
        assert 0 == User.objects.count()
        user = User(
            username='username1', email='email1@email.com', password='123')
        user.add()
        assert 1 == User.objects.count()

    def teardown(self):
        for t in reversed(BaseModel.metadata.sorted_tables):
            sql = 'delete from {} cascade;'.format(t.name)
            Session.execute(sql)
        Session.commit()
        Session.close()
