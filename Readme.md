# Voice squads bot
This bot auto generates a voice channel when there are no more empty voice channels, and also removes them to keep it clean.
It will always leave 1 empty channel, for players to join.
To setup the bot "/admin set category" to set the category where it needs to create the voice squad channels.
Then use "/admin generate initial-channel" to create the initial squad voice channel to work with
And "/admin generate voice-management" to generate the buttons for users to alter the voice channel.
The person that first joins the channel, will be the owner until it\'s empty again.
You can use "/admin names add/list/remove" to overwrite the names of all the voice channel names it creates with your own set.

There is also a public instance of this bot available with the following invite url:
https://discord.com/oauth2/authorize?client_id=1483945839675314257&permissions=274877959184&scope=bot%20applications.commands