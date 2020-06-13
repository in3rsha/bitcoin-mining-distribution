# ImageMagick - VERY SLOW FOR 100+ images
# ----------

# gif with delay on last frame (grab last frame and add it on to the end)
# convert -delay 10 $(ls -v *.png) -delay 290 $(ls -v *.png | tail -1) imagemagick.gif

# Gifsicle
# --------

# convert all pngs to gif first (gifsicle only takes in gif images)
echo "Converting pngs to gifs"
for file in charts/*.png; do
  echo $file;
  convert $file $file.gif
done

# add watermark to each individual image
echo "Adding watermarks to each gif"
for file in charts/*.png.gif; do
  echo $file;
  convert $file -background transparent -fill darkgrey -pointsize 28 -gravity south -annotate +0+0 'github.com/in3rsha/bitcoin-mining-distribution' $file;
done

# create gif (ls -v to get files in natural numerical order)
echo "Creating animated gif"
gifsicle --colors 256 --delay=10 --loop $(ls -v charts/*.png.gif) > mining-distribution.gif

# add delay to final frame (2 secs)
echo "Adding delay to last frame of gif"
gifsicle -b mining-distribution.gif -d10 "#0--2" -d200 "#-1"

# remove temporary gif files from chart/ directory
echo "Removing temporary .png.gif files from charts/ directory"
rm charts/*.png.gif.
