# Project Documentation

## Source Format
This tool is designed specifically for migrating **TiddlyWiki** files. The extraction scripts and data models are optimized for TiddlyWiki's single-file HTML format and tiddler structure.

> **Note:** The comprehensive documentation for this project is maintained in the Obsidian vault at:
> 
> `C:\Users\PhilJ\Nextcloud\Notes\1 Projects\PKM Migration\Wiki Migrator 3`
>
> Please refer to that location for detailed project documentation, architecture decisions, and usage guides.

# Project File Structure
* Transform scripts should be in the `/transforms` folder
* Output folders should all go in the `/output` folder

# Testing Notes
* Default to using `C:\Users\PhilJ\Dropbox\phil-home.html` for all migration tests unless told otherwise
* Every time you do a test run of a transform script, show the JSON data for the following notes:
  * Cars
  * OpenClaw Setup
  * AI Links

# The scripts
The following will be true of all immigration scripts, unless noted otherwise:
1. Every transform script will have an ID, numbered 0 - Z. ALL transform script IDs should have only one character - if we run out of IDs in the ID space of 0 - Z, move to two-character IDs having a leading `0` (example: `0C`).
2. Every transform script will have a name briefly describing what it does
3. The name of every transform script will be its ID followed by its name
4. Every transform script will generate a new folder containing both a JSON document (`_notes.json`) with all note data, and a full export of markdown documents in the folder structure appropriate for this iteration
5. Every transform script will accept exactly one argument
6. The first argument must always be the name of the output folder of a previous experiment run. The output folder name will be the ID of the script that is running a pendant to the name of the folder passed into the first argument.
7. The only script that is an exception to the previous rule is the 0 script, which will be the script that extracts all the notes from the original wiki file. It will only ever need to be run once, and it will generate an output folder named after its ID – `0`.
8. Since all transform scripts must generate a folder containing a JSON document and markdown file files, they will all use the same helper functions to avoid duplicating – and possibly varying – this functionality.
9. Any changes made to any of the transform scripts must result in a new script with a new ID. The name can be the same as the previous copy. But this means that the resulting file name will be different, because the file name contains the ID.
10. The only exception to the above rule will be script `0`, the extraction script. We'll need to iterate on it "in-place" before starting to follow the above rule because getting the data extracted correctly is foundational to the process.