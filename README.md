# beetmatch

A plugin for the [beets](https://beets.io) media library manager that tries to generate playlists from tracks that have
similar properties.

## Installation

The plugin can be installed via pip:

```bash
$ pip install beets-beetmatch
```

To activate the plugin add `beetmatch` to the lists of plugins in your beets config.yaml:

```yaml
plugins:
  - beetmatch
```

### Install Musly (optional)

The plugin supports music similarity computation using [libmusly](https://github.com/dominikschnitzer/musly).
In order to allow beetmatch to use this functionality, libmusly has to be installed first.

Since musly hasn't seen much development recently, you might encounter difficulties with newer compilers.
An updated version of the library, that works with recent versions of Linux and macOS, can be
found [here](https://github.com/andban/musly).

### Helpful Plugins

This plugin works best when it has a set of track attributes that provide addition insight on the audio content of
individual tracks.

- [autobpm] computes the BPM of tracks
- [keyfinder] computes the musical scale of tracks
- [xtractor] uses Essentia to provide multiple properties that can be used for track similarity (BPM, scales,
  danceability, etc.)

## Configuration

This plugin can be configured by providing options in the beets config.yaml under the `beetmatch` section:

- **auto**: automatically analyze imported tracks when musly is available
- **[jukeboxes](#jukebox)**: define jukeboxes that narrow tracks used for generating playlists from, e.g. songs
  within the same genre.
- **[playlist](#playlist)**: defines parameters used for playlist generation
- **[musly](#musly)**: change if and how musly is used for metadata generation

### jukebox

A jukebox is a sub-set of songs in your library, that can be used to create playlists from.
For example, you want to create playlists, which are only generated from songs in the 'electronic' genre.

A jukebox entry is made up of the following attributes:

- **name**: The name of the jukebox.
- **query**: a list of queries that specify which songs should go into the jukebox.

Example:

```yaml
    jukeboxes:
      - name: electronic
        query:
          - 'genre:electronic'
          - 'length:..30:00'
      - name: rock_and_pop
        query: 'genre:(rock|pop|country)'
```

### playlist

The playlist sections defines how playlists are generated.

- **default_script**: Define a default script to be call after a playlist was generated.
- **cooldown**: Define how many songs need to be selected before another song of the same artist or album can be added
  to a playlist.
- **attributes**: Configure which attributes of a song are used for similarity computation and how they should be
  measured and weighted. The available attribute types are described further [below](#attribute-types).

Example:

```yaml
    playlist:
      default_script: '~/.config/beets/scripts/music-create-playlist'
      cooldown:
        artist: 5
        album: 2
      attributes:
        bpm:
          type: BpmDistance
          weight: 0.4
          config:
            tolerance: 0.04
        genre:
          type: ListDistance
          weight: 0.3
        year:
          type: YearDistance
          weight: 0.3
          config:
            max_diff: 5
```

### musly

When libmusly is installed, it's setup for track analysis can be configured in this section.

- **enabled**: Whether to enable track analysis.
- **threads**: Number of threads to use when analysing the library.
- **method**: The algorithm that musly should use for track analysis one of `timbre` or `mandelellis` (not tested).
- **data_dir**: Where to store musly jukebox information inside `BEETSDIR`

Example:

```yaml
  musly:
    enabled: yes
    threads: 2
    method: timbre
    data_dir: beetmatch
```

## Usage

### Update Jukeboxes

In case you want to use libmusly in track similarity computations, you will need to analyze the tracks and update
musly jukeboxes first.
It is recommended to trigger an update whenever you added a lot of new songs to your library, or when you feel that the
results are somehow off.

```bash
$ beet beetmatch-musly --write --update
```

```
Analyze tracks and update musly jukeboxes

Usage: beet beetmatch-musly

Options:
  -h, --help            show this help message and exit
  -u, --update          Update jukeboxes with new musly data
  -w, --write           Write analysis results to meta data database
  -f, --force           [default: False] force analysis of previously analyzed
                        items
  -t THREADS, --threads=THREADS
                        [default: 4] number of threads to use for analysis
```

### Generate Playlists

```bash
$ beet beetmatch-generate --jukebox=<jukebox_name> --tracks=30
```

```
Usage: beet beetmatch-generate

Options:
  -h, --help            show this help message and exit
  -j JUKEBOX_NAME, --jukebox=JUKEBOX_NAME
                        Name of the jukebox to generate playlist from
                        (required)
  -t NUMTRACKS, --num-tracks=NUMTRACKS
                        Maximum number of tracks to add to the playlist.
  -d DURATION, --duration=DURATION
                        Approximate duration of playlist in minutes.
  -s SCRIPT, --script=SCRIPT
                        Call script after playlist was generated.
                        This overrides the default_script defined in the configuration.
  -q QUERY, --query=QUERY
                        A query that is used to select the first song in the playlist.
                        If the query results in more than one song, a song can be selected from the result.
                        In case no query is given, a random sonf from the jukebox is selected.
```

## Attribute Types

### Tonal

This measure considers tracks similar if they use scales that are next to each other in
the [circle of fifths](https://en.wikipedia.org/wiki/Circle_of_fifths).
For example a track that uses a C major scale is considered similar to songs that use F major, G major or A minor
scales.

This example uses the `key` and `key_scale` properties provided by the xtractor plugin:

```yaml
attributes:
  key:
    type: TonalDistance
    weight: 0.2
    config:
      key_scale: key_scale
```

When the scale attribute contains a combinded key/scale, like the attribute provided by the keyfinder plugin. No
additional config is needed.

### BPM

This measure considers tracks similar if their tempo is within a certain `tolerance`.

This example uses the `bpm` property with a 4% tolerance level:

```yaml
attributes:
  bpm:
    type: BpmDistance
    weight: 0.2
    config:
      tolerance: 0.04
```

### Year

This measure considers tracks similar if the year of release is within a certain timespan.

The example uses the `year` property with a maximum distance of 10 years:

```yaml
attributes:
  year:
    type: YearDistance
    weight: 0.1
    config:
      max_diff: 10
```

### Musly

This measure uses libmusly to calculate a similarity based on their timbral properties, i.e. tracks that have a similar
sound.

```yaml
attributes:
  musly_track:
    type: MuslyDistance
    weight: 0.25
```

### Numeric

This measure uses the difference of two numeric track properties as similarity measure. For example the danceability
property provided by the xtractor beets plugin.

```yaml
attributes:
  danceability:
    type: NumberDistance
    weight: 0.1
    config:
      min_value: 0
      max_value: 1
```

### Set

This measure uses the edit difference of two set properties as similarity, like the style or genre properties provided
by the Discogs beets plugin.

```yaml
attributes:
  genre:
    type: ListDistance
    weight: 0.1

```

## Docker Image

```bash
$ docker build -f docker/Dockerfile -t beetmatch .
$ docker run -it \
     -v "${PWD}/examples/docker:/var/lib/beets" \
     -v "<your music folder>:/var/lib/music:ro" \
     -e "BEETSDIR=/var/lib/beets" \
     -e "MUSIC_FOLDER_HOST=<your music folder>" \
     beetmatch:latest

beets@docker:/var/lib/beets$ beet import /var/lib/music
# this should take quite a while
beets@docker:/var/lib/beets$ beet bmm -u -w
beets@docker:/var/lib/beets$ beet bmg -j electronic -t 10
```

After all these commands are done, you should find a rock.m3u playlist in the examples/docker/playlist folder.
