# How to use git?
<div align = "right">by Yujin Lee </div>

## Install Git on Your Computer
- our github repositort: https://github.com/2-ujin/IFN582_grp_assginment

### Windows:
- Go to git-scm.com/downloads and download Git for Windows.
- Run the installer and keep all default options (just click “Next” through the setup).
- After installation, open “Git Bash” from the Start menu to confirm it installed correctly.

### MAC:
- Open Terminal and type: git --version
- If Git is not installed, macOS will prompt you to install the “Command Line Developer Tools” — click Install.


## Clone the Repository

"Cloning” means downloading a full copy of the project (with its full history) onto your computer.

1. Open Git Bash (Windows) or Terminal (Mac).
2. Navigate to the folder where you want to save the project, for example:
```
 > cd Desktop
```
3. Run the clone command:
```
 > git clone https://github.com/2-ujin/IFN582_grp_assginment.git
```
4. This creates a new folder called "IFN582_grp_assginment" containing all the project files. Move into it:
```
> cd IFN582_grp_assginment
```
(I just ask claude to clone the github repository and my local computer, if u guys have clone or other AI tool they might explain better than me )

## How to update & Modify file in the repository? 

1. First Make sure ur local file and main branch repository sync well.
```
> git pull
```
2. modify / create files from ur local side

3. update the files you changed
the staging is add(ready for staging) > commit (labelling)> push (update to main branch)


```
> git add [file name]
> git commit -m "the description of this commit"
> git push 
```