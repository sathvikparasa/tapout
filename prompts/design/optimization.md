
# Goal
Optimize the current UI with updated polling, and remove redundant API calls such as the ones in the feed.

# Details
For the upvote, use optimistic updates so that the numbers change instantly when upvoted, and the server call happens whenever it happens. For the feed, make it such that there's one call to the feed when the feed tab gets clicked, or pull down to refresh, and the subsequent location cliscks on the filters for the locations only filters the resulst, and doesn't call the API for the reports. In the map view, it shows the LOT code twice (e.g. ARC ARC, MU MU), fix it so that it only shows up once, or show the full lot name instead of the ID under the badge. In the homepage, on the select a a location dropdown, it only registers a click if you click on the text, and not the whitespace next to the dropdown.

# Rules 
Don't commit anything without approval.
dont modify xcodeproj files.
