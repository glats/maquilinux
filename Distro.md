

# **Pulsar (codename)**

## *GNU/Linux Distribution*

By **Chris Cromer** & **Oscar Campos**  
**March the 12th of 2022**

[1 GNU/Linux Distribution](#1-gnu/linux-distribution)

[1.1 Codename](#1.1-codename)

[1.2 Releases & Support](#1.2-releases-&-support)

[1.2.1 Biannual](#1.2.1-biannual)

[1.2.2 Long Time Support (LTS)](#1.2.2-long-time-support-\(lts\))

[1.3 Development](#1.3-development)

[1.4 Distributable ISO Images](#1.4-distributable-iso-images)

[1.5 Init System](#1.5-init-system)

[1.6 User Sessions and Seats](#1.6-user-sessions-and-seats)

[1.7 Graphics Toolkit](#1.7-graphics-toolkit)

[1.8 Target Audience](#1.8-target-audience)

[1.9 Initram File System](#1.9-initram-file-system)

[1.10 Packaging](#1.10-packaging)

[1.10.1 Package Distribution](#1.10.1-package-distribution)

[1.10.2 Package Splitting](#1.10.2-package-splitting)

[1.10.3 Package Manager of Choice](#1.10.3-package-manager-of-choice)

[1.11 Kernel](#1.11-kernel)

[1.12 Binary Blobs](#1.12-binary-blobs)

[1.13 Licensing](#1.13-licensing)

[1.14 Repositories](#1.14-repositories)

[1.14.1 Pulsar’s Official Repository](#1.14.1-pulsar’s-official-repository)

[1.14.2 Pulsar’s Community Repository](#1.14.2-pulsar’s-community-repository)

[1.14.3 Third Party Repositories (like users or fedora)](#1.14.3-third-party-repositories-\(like-users-or-fedora\))

[1.15 Supported Architectures](#1.15-supported-architectures)

[1.16 Multilib](#1.16-multilib)

[1.17 Distribution Versioning](#1.17-distribution-versioning)

[1.18 Distribution Installer](#1.18-distribution-installer)

[1.18.1 GUI Installation with Calamares](#1.18.1-gui-installation-with-calamares)

[1.18.2 Advanced Bootstrapping Process (Terminal)](#1.18.2-advanced-bootstrapping-process-\(terminal\))

[2\. Technical Details](#2.-technical-details)

[2.1 Source Repositories](#2.1-source-repositories)

[2.1.1 Third party hosted solutions](#2.1.1-third-party-hosted-solutions)

[2.1.1.1 Github](#2.1.1.1-github)

[2.1.1.2 BitBucket](#2.1.1.2-bitbucket)

[2.1.1.3 Gitlab](#2.1.1.3-gitlab)

[2.1.2 Self Hosted](#2.1.2-self-hosted)

[2.1.3 Source Repositories Conclusion](#2.1.3-source-repositories-conclusion)

[2.2 Stage 2 & 3](#2.2-stage-2-&-3)

[2.3 Pulsar’s Official supported Languages (for internal tooling and users contributions)](#2.3-pulsar’s-official-supported-languages-\(for-internal-tooling-and-users-contributions\))

[2.3.1 Scripting](#2.3.1-scripting)

[2.3.2 Systems Programming](#2.3.2-systems-programming)

[2.3.3 Desktop Applications and side Tools](#2.3.3-desktop-applications-and-side-tools)

[3\. Community Standards](#3.-community-standards)

[3.1 Community Guidelines](#3.1-community-guidelines)

[4\. Financiation Sources](#4.-financiation-sources)

# **1 GNU/Linux Distribution** {#1-gnu/linux-distribution}

This section describes basic visions and goals that we (the core dev team) share and want to accomplish in what is, our ideal GNU/Linux distribution. This section has to be taken as a declaration of intentions, proposal or as a general guide line about what we expect from the distribution.

## **1.1 Codename** {#1.1-codename}

We haven’t decided a name for the distribution yet, as a result, we will refer to it on this document as codename Pulsar Linux, this codename must not be taken as a name proposal but as a way to be able to refer to it while we decide on a proper name.

## **1.2 Releases & Support** {#1.2-releases-&-support}

Ideally, there should be two types of release points in pulsar.

### **1.2.1 Biannual** {#1.2.1-biannual}

Two release points per year, if possible, at specific points in time

### **1.2.2 Long Time Support (LTS)** {#1.2.2-long-time-support-(lts)}

The Long Time Support (LTS for the rest of this document) should have a period of two years span.

## **1.3 Development** {#1.3-development}

There should be a rolling development repository which is constantly updated with updates for packages and custom software built in house to support the distribution. When the time for a new release arrives, this rolling repo will be copied as a snapshot, then frozen except for bug fixes and security patches until it is released.

## **1.4 Distributable ISO Images** {#1.4-distributable-iso-images}

	With the aim of not confuse end users with a plethora of ISO images as well as reduce efforts of maintaining a large park of distributable images, our proposal is to have a maximum of three ISO images with scoped target as defined below:

* Full Desktop Environment (DE) ISO with Cinnamon: this image could be used to test and/or install Pulsar into an user computer or to be used as a live CD, it will feature a full Cinnamon desktop to improve users experience  
* Lightweight DE ISO with LXDE or Mate (depending on the maintenance state of the LXDE project): this image could also be used to test and/or install Pulsar into an user computer, it will install LXDE or Mate instead of Cinnamon  
* Base ISO with pure terminal and/or i3 Window Manager (WM): this image will mainly focus on manual bootstrap style installations. The image will not autostart and will present the user with a plain Terminal where the user will be able to start the installation process or to start an i3 session in case they require graphical interface assistance. This ISO will include some kind of lightweight web browser (still to determine)

## **1.5 Init System** {#1.5-init-system}

	Pulsar is born from our discontent with major GNU/Linux distributions to force the adoption of systemd and its whole ecosystem by their users, we believe in freedom so systemd is diametrically in opposition with those beliefs. Due that fact, Pulsar will not feature systemd as init system but will adhere to an unique init system, it will leave the door open for community driven alternate init systems (others than systemd that will never be allowed) to guarantee the freedom of our users to choose their init system.

	The only officially supported init system by Pulsar will be OpenRC. 

* It supports dependencies unlike other init systems like runit, dependencies are important for a stable system that has the services start in the correct order and to avoid race conditions or service crashes on startup.   
* It is easy to use and understand and not too complex like s6.   
* It is used by many other distributions and it is actively maintained by Gentoo, a major distribution so its support is guaranteed so far.   
* It supports both runit and s6 for its process supervision, so s6 and runit can be installed later and be used in combination with OpenRC.  
* It already contains a great deal of ready to use init scripts both because it is actively maintained and developed by Gentoo and how long it has been around.

## **1.6 User Sessions and Seats** {#1.6-user-sessions-and-seats}

	There is an ongoing investigation/discussion about which path to take regarding this topic. There are only two choices, the e-suite that includes decoupled parts of the systemd ecosystem (namely elogin, eudev and esysusers) or consolekit2. The development and maintenance status of consolekit2 is uncertain, there are reports of Gentoo using consolekit2 and not relying on openrc-init and openrc-shutdown so a bit of investigation and research has to be done before taking a definitive decision about this point. Also, it is very probable that custom patches for DE environments must be provided, this should not be a huge overhead due our decision of supporting a limited set of desktop environments officially. Avoid any kind of systemd ecosystem tools must be a goal even if some of its tools are viable as they do not force the adoption of the whole systemd scope, systemd developers could change this at any moment and that would be a huge problem at a later stage when our dependency on such tools might be unavoidable.

## **1.7 Graphics Toolkit** {#1.7-graphics-toolkit}

	Given the focus on Cinnamon and LXDE/Mate for the DEs, naturally GTK should be the prioritized graphics toolkit. So packaging GTK apps and alternatives should be preferred where possible unless a GTK version just isn’t available. 

## **1.8 Target Audience** {#1.8-target-audience}

	Pulsar target audience will be focused on developers and linux enthusiasts. This doesn’t mean that in order to use the distribution one would need to configure everything manually or be an extremely advanced linux user but hardened knowledge or experience about using other linux distributions would be appreciated. 

	Mechanisms to automatically configure common services on installation will be in place for users to decide if they want to use them or not. They will be enabled by default, but advanced users or experienced system administrators will be able to deactivate them at will to take full control of their services configurations.

## **1.9 Initram File System** {#1.9-initram-file-system}

	There are three major initramfs implementations, mkinitcpio, dracut and initramfs-tools. As far as we know, mkinitcpio author wants to drop support in favor of switching to dracut. This could affect long term plans, and initramfs-tools is not an option as it is deeply tied to Canonical's Ubuntu and the DEB and APT ecosystem. For all of that, dracut will be adopted as it has been designed to be distribution agnostic and it is in a good and healthy spot.

## **1.10 Packaging** {#1.10-packaging}

	Packaging is a huge topic, there is a large number of package managers available for GNU/Linux, some of them work directly on sources, like Gentoo’s portage and emerge, while others provide of already compiled binary blobs and data compressed and organized in specific formats with metadata files that are used later by a target system to unpack and move/install the files into specific locations on the file system and apply actions before and after the installation process.

### **1.10.1 Package Distribution** {#1.10.1-package-distribution}

	Package distribution in Pulsar will be done by compressed and organized pre-compiled binary blobs in a specific package format.

### **1.10.2 Package Splitting** {#1.10.2-package-splitting}

	Package contents will be split by default. This means that docs, man pages, development headers, libraries, binaries and other kinds of extended non essential data will be split into various packages.

### **1.10.3 Package Manager of Choice** {#1.10.3-package-manager-of-choice}

	As already stated, our goal is to be able to split our package contents in as many individual parts as are needed, this greatly helps reduce bloat and required space on disk depending on the usage that our users will give to specific packages installed on their system. We firmly believe that both debian and its derivatives and arch and other pacman distributions got package splitting wrong, arch directly does not split most of the package contents, while debian and derivatives go into confusing users that usually doesn’t know which development header (-dev packages) they need to install that usually ends in support messages being posted in forums or mailing lists.  
	  
	RPM/dnf rich dependencies system can be leveraged to solve this issue. Making use of the advanced dependency resolutions of this package manager, the system will install different “splits” for a given package depending on what the user already has installed in their systems. So, for example, if the user has the “man” package installed in their system and they install the “apache” package, dnf will also install “apache-man” as a dependency.

	This system is intelligent and allows us to avoid adding myriads of “optional dependencies” to every single package as the package manager is able to figure out which dependencies are needed depending on what the users have installed already in their systems. This is also extended to other actions like, if in a further date the user uninstalls the “man” package, dnf will also uninstall all the “\<package\>-man” installed packages in the system as they are not necessary anymore. 

	For development packages, we will have a dev meta package, if that meta package is installed in the target system, installing software that comes with development headers will always install those for us automatically as the package manager understands we are interested in development as the meta package is present in our system. Previous behavior about uninstalling packages will also be followed if one uninstalls the dev metapackage. The same approach can be followed for other metapackages.

	This also will be applicable to language packages and .po/mo files. They will be split into language packages and based on which language meta package users have installed in their systems, only those language packages will be installed instead of installing all of the available languages on the package. In case of the user wanting or needing to install support for a language that is not globally installed in their system, they could always install said language package manually.

	This will save a precious amount of disk space and make the distribution more suitable and/or attractive to build base Docker images with it, after all, we are aiming to create a distribution whose main objective target are developers.

Having said that, we do not discard the idea of creating our own RPM frontend or whole package manager in the future if RPM and/or dnf does not fits our use case and ultimate goals or if policies about it changes over time (like hard dependency on systemd for example).

## **1.11 Kernel** {#1.11-kernel}

	Pulsar will always stick to the latest stable release of the Linux kernel in each release. The only exception will be for LTS releases. Pulsar will retain both the original kernel from when the LTS version was released and an updated kernel to support new hardware that might have been released during the two years period span.

## **1.12 Binary Blobs** {#1.12-binary-blobs}

	Driver and firmware binary blobs will be available in Pulsar’s official repos. This, for example,  will prevent users from being unable to install or test the distribution due missing GPU drivers in case that open source drivers do not work in some devices as it happens usually with nouveau drivers and some devices. We love free software and we fully support and commit to it, but we believe that giving the best possible experience to our users is above dogmatism even if that means we will not be listed as a FSF Linux distribution; it is a price we are willing to pay.

	This is quite different from our rejection of systemd as init system, in the case of systemd, users are tied to it and are not free to decide which other parts of their systems they want to use as the scope of systemd grows more and more without control each day. Any user will be free to choose to not install any non-free package from Pulsar’s repositories as no non-free package will be essential for the user’s system so the choice will be always present.

## **1.13 Licensing** {#1.13-licensing}

	Any source code that could be generically be used by third party distributions will be licensed under any version of the GNU Public License GPL. For other kinds of software that we produce (or that users contribute) we will be licensing with any of BSD 3-Clause, MIT and/or Apache2 licenses.

## **1.14 Repositories** {#1.14-repositories}

	Pulsar will have only two different repositories.

### **1.14.1 Pulsar’s Official Repository** {#1.14.1-pulsar’s-official-repository}

	This will be our official repository and the one the Pulsar’s developers maintain.

### **1.14.2 Pulsar’s Community Repository** {#1.14.2-pulsar’s-community-repository}

	This will be maintained by trusted users that will serve also as a repository where other unofficial (by the Pulsar’s developers) packages for alternative init systems or Desktop Environments reside. This repository will be maintained by the Pulsar community.

### **1.14.3 Third Party Repositories (like users or fedora)** {#1.14.3-third-party-repositories-(like-users-or-fedora)}

	Pulsar will not support any kind of third party repositories and taking into account that there are no other non systemd RPM based distributions this will be heavily discouraged.

## **1.15 Supported Architectures** {#1.15-supported-architectures}

	Pulsar will be primarily targeting x86\_64 CPU architecture. Other architectures could be provided by the community but none other than x86\_64 (aka amd64) target will be supported officially, at least from the beginning. We do not discard support for other architectures as ARM64 in the future but it is out of scope for the moment.

## **1.16 Multilib** {#1.16-multilib}

	Pulsar will support the execution of 32-bits x86 architecture binaries. This makes Pulsar an x86 multilib distribution.

## **1.17 Distribution Versioning** {#1.17-distribution-versioning}

	ISO release versioning will simply follow a numerical Major and a Minor version for LTS (like 15, 15.1, 15.2, 16, etc), and just a major version for regular ISO. If there are patches or updates in a version that has already been released, the non LTS ISO will be recreated but its version will not be changed.

## **1.18 Distribution Installer** {#1.18-distribution-installer}

We will have two different setups for installing the distribution in end user computers.

### **1.18.1 GUI Installation with Calamares** {#1.18.1-gui-installation-with-calamares}

The default and preferred mode of installation will be using the Calamares Installer that will be available in both full DE and lightweight DE installation media. Calamares has been chosen for its wide support, distribution agnosticity and modular design.

### **1.18.2 Advanced Bootstrapping Process (Terminal)** {#1.18.2-advanced-bootstrapping-process-(terminal)}

Advanced users will be able to use a Terminal based bootstrapping process to take full control of their installation process, this will be available in all the ISOs but will be the only way to install in the base ISO (unless the user manually install Calamares and all of its dependencies inside the ISO before installing and uses Calamares instead) 

# **2\. Technical Details** {#2.-technical-details}

This section will cover how we plan to solve the technical challenges that building a brand new GNU/Linux distribution from scratch presents and which different options we have available to work with, this is an open document, what means nothing that has been written here is written in stone so things might change dynamically as we advance and discuss it.

## **2.1 Source Repositories** {#2.1-source-repositories}

	The source code for both the distribution staging toolchain, our tooling, and packages will be publicly available in a modern git repository provider. There are multiple choices available both self hosted or hosted by third parties. The decision of using self hosted or third party hosted solution will depend in great measure on our choices of financing that at the moment of writing this lines are nil.

### 	**2.1.1 Third party hosted solutions** {#2.1.1-third-party-hosted-solutions}

	There are great git hosting solutions that offer their services for free, with more or less features and capabilities, Pulsar will need a pipeline capable git service provider so hosts like NotABug.org that only provides of simple source code repository hosting are discarded by default, this only leave us with three possible providers (that we know), Github owned by Microsoft, BitBucket owned by Atlassian and Gitlab owned by Gitlab.

#### 	**2.1.1.1 Github** {#2.1.1.1-github}

	Github grew in popularity really fast after its initial release in 2008, some of the biggest open source projects on earth are hosted on it. Despite that popularity, from our three choices Github is the least mature in when it concerns pipelines. For many years it didn’t had any native support for them relying in third party services such as Circle CI, Drone CI or Travis CI and just recently they incorporated Github actions that aims to solve the situation but does not feels like a real CI/CD solution on par with those offered by both BitBucket and Gitlab

#### 	**2.1.1.2 BitBucket** {#2.1.1.2-bitbucket}

	In the other hand, BitBucket offers a fully JIRA and other Atlassian’s products integrated solution (it’s obviously due the fact that Atlassian’s is the owner and developer of BitBucket) that can also integrate well with third party solution providers as AWS, Azure and many others, they have a limit for their free tier of 50 minutes of runners execution limit per month and it is not clear if they have any other policies for FOSS projects, we looked for it for some time but were not able to find anything.

#### 	**2.1.1.3 Gitlab** {#2.1.1.3-gitlab}

	Gitlab offers the best solution for pipelining for FOSS projects, they offer fifty thousand minutes per month on their free tier for public projects, one million two hundred and thousand minutes for their premium and six million two hundred and fifty thousand for their ultimate. Gitlab pipelines are the most mature and powerful solution in the market nowadays with many years of experience.

### 	**2.1.2 Self Hosted** {#2.1.2-self-hosted}

	There are many options for a self hosted solution, including Gitlab community edition, Gitea plus Drone CI and others. The only problem with self hosted solutions is that we need our own hardware to run the building process and that is far from ideal as we do not have resources to accommodate and the ones we have are lent out to the Artix Linux project.

### **2.1.3 Source Repositories Conclusion** {#2.1.3-source-repositories-conclusion}

	My suggestion is to host all of our source code and building pipelines in Gitlab, also reach them to see if they would be willing to sponsor Pulsar linux giving us free premium or ultimate access in exchange of having a successful use case of a whole Linux distribution being developed, crafted and built in their infrastructure.

## 	**2.2 Stage 2 & 3**  {#2.2-stage-2-&-3}

TBD how we are gonna approach stages 2 and 3 for Pulsar

## **2.3 Pulsar’s Official supported Languages (for internal tooling and users contributions)** {#2.3-pulsar’s-official-supported-languages-(for-internal-tooling-and-users-contributions)}

	We shall define a clear technological stack we use for both our tooling and the contributions we accept from our users. This way we can avoid users trying to contribute software, tooling or patches written in languages that we do not usually have in mind a part of our stack, like Java, Ruby, PHP etc, I propose the following languages and areas to be accepted and used as part of our technological stack

### 	**2.3.1 Scripting** {#2.3.1-scripting}

	Scripting will be used mainly to glue different parts together, for toolchains, packaging and other many tasks that both BASH scripting and Python can come handy. Said that, we shall limit the usage of non memory safe languages as much as possible and make sure parts of our systems written in them are fully covered by tests. I suggest we allow and support the following scripting languages:

* BASH Scripting (preferred)  
* Python

### 	**2.3.2 Systems Programming** {#2.3.2-systems-programming}

	We shall embrace the usage of memory safe languages in opposition to C and C++, C is great for writing low level code but it comes with many issues due its low level and memory management design, same can be said for C++. I suggest we allow and support the following system languages:

* Golang (preferred)  
* C++ (rpm plugins)


### 	**2.3.3 Desktop Applications and side Tools** {#2.3.3-desktop-applications-and-side-tools}

* Vala  
* We might also accept Go bindings for GTK

# **3\. Community Standards** {#3.-community-standards}

Pulsar aims for an inclusive and safe community, in order to achieve this goal some guidelines and rules will be in place.

## **3.1 Community Guidelines** {#3.1-community-guidelines}

The following description and Community guideline will be posted in all of our communication channels and Community websites.

*The aim of this Community is to **build a welcoming, safe and productive space for every user and contributor**. We are here to build **amazing Free Software** together and to enjoy as much as possible during the process.*

*We encourage contributions from **anyone** who wishes to contribute in any avail with the project, **regardless of gender, race, religion, cultural background, and any other demographic characteristics, as well as political or personal views**.*

*For the above to be possible we **must treat each other with kind and respect**, some general guidelines must be followed.*

***General Guidelines***

- *Be kind to each other, assume that behind the nickname you see in your screen are real people, be respectful*  
- *Assume that others act in good faith, specially if you disagree with what they are saying*  
- *Do not mock a question or a help request no matter how simple you might believe it is. If you cannot stay nice, please, walk away*  
- *Use the English language only, unless you are in an international channel that might accept other languages, we all need to understand each other*  
- *Do not make fun of non English native speaker accents or way of speaking, if you do not understand something ask kindly to repeat the sentence*  
- *You must follow the Community rules at every moment*

***Community Rules***

- *Respect other users, no hate speech will be tolerated in this Community*  
- *Do not discuss about religion, beliefs or politics, including the off-topic channels, this is no place for that*  
- *Do not make “jokes” that might be considered offensive and target specific groups, ethnicity or collective, if you don’t have anything nice to say, stay silent*  
- *No drama. Do not speak badly about other distributions, operating systems or developers*  
- *Maintain memes and comments about systemd at a bare minimum, we all here dislike it already*  
- *Use the right channels in the right way, there is a channel for every topic*  
- *No spam or self-promotion, public or private*  
- *No harassment public or private will be tolerated*  
- *Do not fall in dynamics of disruption of discussions, talks or other events*  
- *Intimidation or bullying will not be tolerated*  
- *Unwelcome sexual attention will not be tolerated*

# **4\. Financiation Sources** {#4.-financiation-sources}

No sources of financing so far