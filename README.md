# PyroSync 🎆

PyroSync is a simple program that allows you to sync any music with timecodes pursuing the goal to help you sync your shots with the music.

This code has been made to be used with this kind of firing system using districts and lines : https://www.amazon.fr/dp/B07DBJMT9B?psc=1&ref=ppx_yo2ov_dt_b_product_details


## Files
`hand_pyro.py` is the main program.
`config.csv` is the config file used by hand pyro for syncing.
`audio.mp3` (not included here) is the audio you want to play.

## Requirements
Before using, please ensure you have VLC installed on your computer :
Download here : https://www.videolan.org/vlc/index.fr.html

Install python libraries:

    pandas 
    datetime
    vlc 
    TermTk
## Config
Sample of a config file 
```
    timecode,district,lines,firing_type
    00:00:00,1,"[1]",unit
    00:00:02,2,"[1,2,3]",rapid
    00:00:06,3,"[1,2,3]",all_fire
```
The program is precise down to the second.
`Unit` -> Single line
`Rapid` -> Multiple lines with a delay between each
`All` Fire -> Will shoot all lines in a Disctrict

Please ensure there's no line after the end of the audio or it will crash.

## Improvements & Known bugs
### Improvements
This program has initially been made to be used with an unofficial remote control such as Flipper Zero for the receivers after reverse engineering the signals and bytes.
Unfortunately and mostly due to time I did not had the possibility to implement this.

This is why there's the different lines and type of firing inside the code.

If you want to contribute, please fork the repo and open a pull request, I'll be happy to merge your request if relevant ;)

### Known bugs
If you start the program, then start the show, central timer will not start. Please stop, reset then start again and it will start.
