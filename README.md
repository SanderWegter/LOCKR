# LOCKR

Tool for industry things. Will add more features later

## Requirements
* Python dependencies
```
pip install esipy
pip install flask
```
* An application Client- and secret key from [CCP Developers Page](https://developers.eveonline.com/applications)
* Set your callback url on the ccp developers page (eg. http://yourhostname.com:12345/oauth/)

## Usage

* Copy config.yaml.example to config.yaml `cp config.yaml.example config.yaml`
* Add the client/secret keys and callback URL to config.yaml
```
chmod +x app.py
./app.py
```
Browse to http://yourhostname:12345/ and use the eve SSO to log in. 

Information on what ESI endpoints are available, please visit the [ESI page](https://esi.tech.ccp.is/latest/).

## Todo
* Add (proper) installation guide
* Add usage guide
* Add more examples
* Add graphs
* Add history tracking (from wallet history and prospected sales)
* Pretty log-in page

### Thanks
Using [EsiPy](https://github.com/Kyria/EsiPy)

If it helped, isk donations can go to madpilot0 :-)

# CCP Copyright Notice
EVE Online and the EVE logo are the registered trademarks of CCP hf. All rights are reserved worldwide. All other trademarks are the property of their respective owners. EVE Online, the EVE logo, EVE and all associated logos and designs are the intellectual property of CCP hf. All artwork, screenshots, characters, vehicles, storylines, world facts or other recognizable features of the intellectual property relating to these trademarks are likewise the intellectual property of CCP hf. CCP hf. has granted permission to DOTLAN EveMaps to use EVE Online and all associated logos and designs for promotional and information purposes on its website but does not endorse, and is not in any way affiliated with, DOTLAN EveMaps. CCP is in no way responsible for the content on or functioning of this website, nor can it be liable for any damage arising from the use of this website.