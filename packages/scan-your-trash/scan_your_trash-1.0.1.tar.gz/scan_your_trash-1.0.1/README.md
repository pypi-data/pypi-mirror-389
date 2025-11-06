# Scan Your Trash

This library helps extract data from samples created with the [Scan Your Trash](https://scanyourtrash.de) app.

## Using as command line tool

After installing this package you will get access to the `scan-your-trash` command line tool.

### Syncing files from s3 to disk

The sync command downloads any samples on the s3 bucket that aren't already on your disk. It ignores files that already have been downloaded.

It's recommended to install the [awscli](https://pypi.org/project/awscli/) utility when using this functionality.

1. Make sure you log in to the s3 bucket: `aws configure --endpoint https://landfill.scantrash.de`
2. Start a sync job: `scan-your-trash sync <bucket-name> ./`

### Unpacking a sample into frames

1. Make sure you have a folder to store the unpacked results: `mkdir unpacked`
2. Unpack the sample: `scan-your-trash unpack 4/54E2CF4C-3E61-483B-91C9-D668D2E76537.mov unpacked`

## Using as a library

Example:

```python
from scan_your_trash import Reader

with Reader("4/54E2CF4C-3E61-483B-91C9-D668D2E76537.mov") as r:
  print(r.get_metadata())
```

Reader exposes the following methods:
 - `get_recycling_logo()` - Returns None or the recycling logo photo as PIL.Image
 - `get_metadata()` - Returns the global metadata for the sample
 - `get_samples(compute_mask = True)` - Yields frame samples: `(timestamp, main_frame, depth_frame, saliency_frame, object_mask, frame_meta)`

