# RE-Dualsub-Tool

Python scripts to make dual-subtitle mod (like [this](https://www.nexusmods.com/residentevil42023/mods/284)) for RE Engine games.  

> This repo is a work in progress, and hard to use now.  
> Wait for updates.  

## Setup

### 1. Get REMSG_Converter

Clone [REMSG_Converter](https://github.com/dtlnor/REMSG_Converter) with `git submodule update --init`.  
Or copy its python scripts into `./REMSG_Converter`.  

### 2. Remove dependencies

Move to `./RE-Dualsub-Tool`.  
Then, type `python src\remove_dependencies.py`.  
It'll remove mmh3 and chardet functions from REMSG_Converter.  
And it'll copy the edited files to `./src`  

## Scripts

There are some scripts in `./src` folder.

- `run_retool.py`: Script to extract UI related files from `*.pak`.  
- `make_dualsub.py`: Script to merge a language's text to other languages' text.  
- `edit_fslt.py`: Script to convert between *.fslt and *.json.
- `edit_gui.py`: Script to convert *.gui to *.json. (No function for json2gui yet.)

## Credits

- FluffyQuack's REtool for file extraction.
- dtlnor's [REMSG_Converter](https://github.com/dtlnor/REMSG_Converter) for .msg editing
- alphaZomega's template to get hints for *.gui.540034 structure.
