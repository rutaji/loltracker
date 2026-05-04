# SQL specification

This documentation is relevant for alembic versions until: ``9a4b6c7d8e90``

## Champion

This table is about the playable characters in League of Legends, which are called Champions.

```id``` is a String identifier used by the Riot API. In most cases it is the same as ```name``` used in game, but there are exceptions (e.g. Wukong's ```id``` is MonkeyKing as opposed to Wukong).

``champion_key`` is a unique integer value for each Champion used in **Ban** and **Champion_Match_Ban**.

## Champion_Stats

This table exists for tracking statistics about individual Champions to provide users with analysis of win rate, pick rate, ban rate and KDA over multiple game versions.

```champion_id``` is the ``id`` used in the **Champion** table.

```patch``` and ```queue_id``` are the game version and game mode to which the statistics belong.

The remaining fields are all incremented based on the data in **Match_Participant** entries using ```champion_id``` from **Match_Participant** and ```gametype``` and ```patch``` from **Match**.

## Summoner

This table is about the player accounts in League of Legends which are referred to as Summoners.

```id``` corresponds to the ```puuid``` tag in data recieved from Riot API.

```name``` is the in game player name.

The remaining fields are all values that get incremented each time a given **Summoner** ```id``` appears in a new entry in the **Match_Participant** table.

## Summoner_Queue

This table keeps track of a player's performance in Ranked play of League of Legends.

``summoner_id`` and ``queue_id`` are foreign keys corresponding to entires in **Summoner** and **Queue**

``tier`` correponds to divisions used within LoL such as "EMERALD", "GOLD", "MASTER", etc

``rank`` is a value between 1 and 4 that creates more levels within most divisions. Some divisions don't have ranks and for these divisions the value is irrelevant (omitted by frontend)

``league_points`` are used to determine whether a player will move up or down a division

``wins`` and ``losses`` are self explanatory

## Summoner_Champion

This table exists to keep track about how many times each Summoner played each Champion.

```summoner_id```, ```champion_id``` and ``queue_id`` are foreign keys that point to entires in the **Summoner**, **Champion** and **Queue** tables respectively.

The remaining attributes are counters incremented via trigger based on data in **Match_Participant**.

## Queue

This table contains informtion about each possible game mode in League of Legends.

All fields in this table correspond to data used in the Riot API.

## Match

This table contains entries for the individual games of League of Legends that were played.

```id``` corresponds to the ``matchId`` tag in data recieved from Riot API. 

```queue_id``` is the foreign key of the concrete game mode.

```created``` is unix time in seconds at which the match started.

```ended``` is unix time in seconds at which the match ended.

```patch``` is the game version on which the match was played.

## Match_Participant

This table contains data relevant to each player that partook in a given game of League of Legends.

```summoner_id```, ```match_id``` and ```champion_id``` are foreign keys belonging to entries in the **Summoner**, **Match** and **Champion** tables respectively.

```kills```, ```deaths```, ```assists``` and ```gold``` correspond to the match statistics of the given player and are recieved from Riot API.

```team``` is equal to the ``teamId`` tag used in Riot data.

```won``` is a boolean value equal to the ``win`` tag used in Riot data.

``position`` corresponds to the in-game roles a player can have such as "TOP", "BOTTOM", "SUPPORT", etc.

Fields ``item0`` to ``item6`` and ``role_bound_item`` correspond to in game items held in the **Item** table.

## Matches_Analyzed

This table acts as a way for the system to keep track of how many games were saved into the database. This information is necessary for the calculation of the win rate, pick rate and ban rate statistics.

```patch``` and ```queue_id``` corrsepond to the same data as those in **Match**.

```count``` keeps track of the number of saved matches for each ```gametype``` and ```version``` and is incremented via trigger each time a new **Match** is added to the database.

## Ban

This table exists to keep track of Champion bans made in games of League of Legends.

``match_id`` is the foreign key of the **Match** in which the ban took place.

``team`` is the team number used by Riot that created the given Champion ban.

``champion_key`` is the Champion identifier for the ban. This is used by Riot instead of **Summoner** ``id``.

## Champion_Match_Ban

This table is a sloution for a bug that caused duplicate bans (both teams banned the same Champion) to cause a crash.

``match_id`` is the foreign key of the **Match** in which the ban took place.

``champion_key`` is the Champion identifier for the ban. This is used by Riot instead of **Summoner** ``id``.

## Item

This table contains basic information about every item available for purchase in LoL.

``item_id`` is a unique integer value for each item and is recieved from data created by Riot.

``name`` and ``description`` are given to each item by Riot.

## Indices

Below is a rundown of the indices present in the database.

**Champion** - ``id``, ``name`` and ``champion_key``

**Champion_Stats** - ``champion_id``, ``patch`` and ``queue_id``

**Summoner** - ``id``

**Summoner_Queue** - ``summoner_id`` and ``queue_id``

**Summoner_Champion** - ``summoner_id``, ``champion_id`` and ``queue_id``

**Queue** - ``id``

**Match** - ``id`` and ``queue_id``

**Match_Participant** - ``summoner_id`` and ``match_id``

**Matches_Analyzed** - ``patch`` and ``queue_id``

**Ban** - ``match_id``, ``team``, ``ban_order`` and ``champion_key``

**Champion_Match_Ban** - ``match_id`` and ``champion_key``

**Item** - ``item_id``


## Triggers

Below is a rundown of the triggers used in the database.

**Chmapion_Stats** - increments ``games_played``, ``games_won``, ``kills``, ``deaths`` and ``assists`` after insert into **Match_Participant** (uses Riot data)

**Champion_Stats** - increments ``games_banned`` after insert into **Ban**

**Summoner** - increments ``games_played``, ``games_won``, ``kills``, ``deaths`` and ``assists`` after insert into **Match_Participant** (``games_won`` is only incremented if the Summoner won)

**Summoner_Champion** - increments ``games_played`` and ``games_won`` after insert into **Match_Participant** (``games_won`` is only incremented if the Summoner won)

**Matches_Analyzed** - increments ``count`` after insert into **Match**

**Champion_Match_Ban** - does not create a new entry after insert into the table on conflict with data that already exists

## Other

The **Champion** table is filled with each playable Champion when the database is created as part of the alembic migrations.

The **Queue** table is filled with each possible game mode when the database is created as part of the alembic migrations.

The **Item** table is filled with each existing item in LoL when the database is created as part of the alembic migrations.