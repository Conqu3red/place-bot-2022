# r/Place 2022 Bot
This custom-written bot valiantly defended the PolyBridge location and other personal banners for me.

All accounts must be added to script apps [here](https://reddit.com/prefs/apps), limit of 20 accounts per app. The bot ignores pixels in reference images colours exactly (80, 20, 60) / #50143c.

# Config
`board` is the board index:
- `0` - Top Left
- `1` - Top Right
- `2` - Bottom Left
- `3` - Bottom Right

`offset` is the top left corner of the image, relative to the board. For example, a position of (1500, 1500) becomes board: 3, offset: (500, 500)

Each account must specify which app it is connected to, specified as an index into the apps arrray.

All accounts should have an offset of [0, 0], the bot does not treat offsets correctly and there is no point in fixing it.

# Placement Process
Every 10s, if the bot has a pixel to place, it searches for the first incorrect pixel in the image, going row by row, and from left to right. As soon as it finds an incorrect pixel it places the correct one. Account tokens are automatically refreshed when they run out.