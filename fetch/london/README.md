# Fetching London Subway Data

As I recall, **London** might have been a case of abject failure getting
data from the __London Subway Authority__.  Whether by historical accident or
conscious choice, their transportation authority followed a __sui generis__ 
approach to its data format and access.  This might be unfair, and should
be validated.  It has consequences.  While more humorous
rather than a quantification of difficulty in dealing with the __London Subway native API__
and format, threads on various technical sites are strewn with developers pulling
out their hair with questions of fundamental usage.  So at least in this project this
was an open invitation, if not a demand, to seek an alternate source of information.

Enter __Overpass__, an __OSM__ network __API__ which is __community-build__.

First, let's acknowledge that this is great in that this exists at all.

Second, you have to evaluate your overall target.  If you are going after
an __enchilada__ that includes schedules and (ominously) __routes__ then
you should take it as a given that you will meet a hard-boundary.  So we shall
see about the outcome of binding __stations__ to __lines__ (maybe a colloquial usage
borrowed from __NYC__ where subway lines are called __lines__).

We will see if that is true.  We really do not want to explore even the
boundary of __computational geometry__ for doing something as simple as
finding what __line(s)__ a __stop__ belongs to.

## Fetch

This is a real network fetch (as opposed to a static data download of files).
Seeing the code in `fetch_london_tube_overpass.py` we establish __mirror__
sites in an ordered list.  Notice that these mirrors __have nothing to do
with an authority in London__.  In fact, they are prefixed with **overpass**:

> Overpass is a read-only API for querying OpenStreetMap (OSM) data using a custom query language.

So we have an __OpenStreetMap__ __DSL__.  And this is where __ChatGPT__(hereafter __Le Chat Noir__)
shines.  It would be truly difficult to figure out - without a decent day of reading
documentation (which would also give you a better overview, admittedly), that the way
to gather subway data from the London Underground in __JSON__ format would be
to form __query strings__ specifying:

-- type of transportation (not quite, since it is route=subway, but close enough)
-- general name for location or authority (London Underground)
-- (Latitude, Longitude) bounding box (this is actually a nice touch)

The (Latitude, Longitude) bounding box (BBOX) is defined for
Greater London bbox (S, W, N, E).  However, one would hope that
this is how __BBOX__ is defined for every locale.

```
Q_IDS = f"""
[out:json][timeout:120];
relation["route"="subway"]["network"="London Underground"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
out ids;
"""
```

This is a __query string__ to retrieve a set of ids.

## Getting London Station Data into Memory

This is done using the exact same __DSL__ format to build the __query string__:

```
STATIONS_Q = f"""
[out:json][timeout:120];
(
  node["station"="subway"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  node["railway"="station"]["subway"="yes"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out body;
"""
```

Then there is an absolutely off-the-wall __query construction__ wrapped in the function `q_members`.
To clarify: the mechanisms and flow of the __query construction__ are of the highest quality;
the __query format__ is **bonkers**.  These are the steps:

-- Uses `range(0, len(ids), batch_size)` for looping through batches.
-- For each batch uses `",".join(str(x) for x in batch)` to place these ids as a `<tuple>` in an `id_list`
-- Places these `id_list` `<tuple>` types containing ids in a `chunks` `<list>` (so a `<list>` of `tuple`).  In pseudo-code (I do not believe Python has generics, this would be expressed as `list<tuple>`
-- The `chunks<list>` is then __flattened__ into a single `string` with each item separated by a new line (So `<tuple>` as comma-separated string `\n` `<tuple> as comma-separted string` `\n` + ...
-- Up to this point this is just nice, compact coding.   __AI__ **ars adeo latet arte**.
-- The __query__ is **bonkers**.  While it is written out expansively, it is really: `"""[out:json][timeout:240]; ({body}); out body; ; out skel qt; """`

# Workflow

To pull back to a function sequence or function workflow view we have two essential pathways:

-- `fetch_with_fallback`->`post_stream`  
-- `fetch_json_with_fallback`->`post_stream`  


The quality of the code is __very good_.  Amazingly tight.  Well designed.  If
I saw this in the __days before the machines took over__ I would say this is a
senior developer who is of outstanding caliber in the craft of programming.
Someone you would give some piece of functionality already written and who
would then put it in the 98% percentile of compact and tight code expression
using the idioms of the target language: that is, taking care of a large number
of issues in the smallest amount of space with the code readable in terms of
its units of expression.  It seems ridiculously quibbling - and even great
programmers do not always do this (some philosophically) - but the functions do
not name exactly what they do.

This prompts the guess that there are a number of really high quality
repositories out there.  Would this not make sense.  They are constantly
gathering the same information in a small __DSL__ from the same server (with
the same syntax and properties of chunked responses).

## 🛰️ Function: `post_stream`

This Python function is designed to stream large HTTP POST responses from services like the [Overpass API](https://overpass-api.de) and save the data directly to disk. It includes real-time progress tracking, stream-safe chunked handling, decompression support, and detailed error handling.

### Signature

```python
def post_stream(url, data, out_path, chunk=4<<20, progress_every=0.5):
```
-- chunk is an int quantifying Chunk size in bytes (default: 4 << 20 = 4 MiB).
-- progress_every is a float (seconds) specifying how often to print progress updates (default:?)

### ⏱️ Timer and Counter Setup

The function starts by initializing timers and counters for download tracking:

```python
t0 = time.time(); n = 0; last_t = t0; last_n = 0
```
-- t0 records the start time of the entire download.
-- n is the cumulative number of bytes downloaded.
-- last_t and last_n record the time and byte count of the last progress update, used to calculate instantaneous speed.

### 📤 Streamed HTTP POST Request

The function sends a streamed HTTP POST request to the target endpoint:

```python
with requests.post(url, data={"data": data}, stream=True) as r:
```
-- requests.post sends a form-encoded field data="...your Overpass query..." to the server.
-- stream=True tells requests not to download the entire response at once, but to iterate over it chunk by chunk — crucial for very large responses.

### 🛑 Robust Error Handling

Immediately after receiving the response, the function checks for HTTP errors:

```python
try:
    r.raise_for_status()
except requests.HTTPError as e:
    body = ""
    try: body = r.text[:2000]
    except: pass
    raise RuntimeError(f"Overpass error at {url}: {e}\n--- server said ---\n{body}") from None
```
-- `r.raise_for_status()` raises an error if the HTTP status code indicates a failure (400–599).
-- If an error occurs, the code attempts to extract up to the first 2000 characters of the response body for debugging.
-- It wraps the exception in a RuntimeError with the URL and snippet, making Overpass API issues easier to diagnose.

### 🧪 Automatic Decompression

```python
r.raw.decode_content = True
```
This ensures that if the server sent a compressed response (e.g. Content-Encoding: gzip), requests will transparently decompress it as the chunks are read.

```
with open(out_path, "wb") as f:
    for b in r.iter_content(chunk_size=chunk):
        if not b: continue
        f.write(b); n += len(b)
```
-- Opens the target file in binary write mode.
-- Iterates over the response content in chunk_size bytes (default 4 MiB).
-- Skips empty chunks (some servers send heartbeat keep-alive packets).
-- Writes each non-empty chunk to disk and increments the downloaded byte counter.

### 📈 Real-Time Progress Reporting

Every `progress_every` seconds, the function prints human-readable statistics:

```python
now = time.time()
if now - last_t >= progress_every:
    dt = now - t0
    inst = (n - last_n) / (now - last_t) if now > last_t else 0
    avg = n / dt if dt > 0 else 0
    print(f"⬇️  {human(n)} in {dt:.1f}s | inst {human(inst)}/s, avg {human(avg)}/s")
    last_t = now; last_n = n
```
-- Total downloaded: formatted via human(n) (e.g. 45.2 MB)
-- Elapsed time: since t0
-- Instantaneous throughput: bytes downloaded since the last print divided by time interval
-- Average throughput: total bytes divided by total time

### ✅ Completion Summary

After the stream ends, a final summary line is printed:

```python
print(f"✅ Downloaded {n:,} bytes in {time.time()-t0:.2f}s → {out_path}")
```

This includes total bytes downloaded (with thousands separators), total elapsed time, and the destination file path.

### Response Body Debugging

If the downloaded file is suspiciously small (< 2 KiB), the function attempts to print its contents for debugging:

```
if n < 2048:
    try:
        print("--- tiny response body ---")
        print(Path(out_path).read_text(errors="replace"))
    except Exception:
        pass
```

This helps diagnose server-side errors where the API returned an error message instead of expected data.

### 💡 Human-Readable Byte Formatter

The function assumes the presence of a `human()` helper:

Two methods were actually written.  This is the method __Le Chat Noir__ **guessed**.
This actually says alot.  Like, its information on how to do this is **tight**.
I am guessing a small number of really high-grade repositories.

```python
def human(n):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"
```

This was the actual method written a month ago and in the code base:

```
def human(n):
    for u in ("B","KB","MB","GB","TB"):
        if n < 1024 or u == "TB": return f"{n:.2f} {u}"
        n /= 1024
```

