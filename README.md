# beetmatch

A plugin for the [beets](https://beets.io) media library manager that tries to generate playlists from tracks that have
similar properties.

## Installation

The plugin can be installed via pip:

```bash
$ pip install beets-beetmatch
```

To activate the plugin add `beetmatch` to the lists of plugins in your beets configuration:

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

## Usage

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
                        Maximum number of tracks
  -d DURATION, --duration=DURATION
                        Duration of playlist in minutes (its not a hard limit)
  -s SCRIPT, --script=SCRIPT
                        Call script after playlist was generated
  -q QUERY, --query=QUERY
                        The first track to base playlist on
```

### Analyze Tracks

In case musly should be used to determine track similarity, all tracks need to be analysed first:

```bash
$ beet beetmatch-analyze -w
```

```
Usage: beet beetmatch-analyze

Options:
  -h, --help            show this help message and exit
  -w, --write           Write analysis results to meta data database
  -f, --force           [default: False] force analysis of previously analyzed
                        items
  -t THREADS, --threads=THREADS
                        [default: 4] number of threads to use for analysis
```

### Update Jukeboxes

To allow musly to compute track similarity, it uses a sample set of each jukebox:

```bash
$ beet beetmatch-update -w
```

## Attribute Distances

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
beets@docker:/var/lib/beets$ beet bmj -u -w
beets@docker:/var/lib/beets$ beet bmg -j rock -t 10
```

After all these commands are done, you should find a rock.m3u playlist in the examples/docker/playlist folder.
