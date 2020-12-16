import matplotlib.pyplot as plt      # Plotting charts
import json                          # Decoding known_miners.json file
import hashlib                       # Hash Functions (for creating colors)
import datetime                      # Convert block Unix timestamp to a date
import colorsys                      # Convert HSV colors to RGB colors

# Python 2.7: Make a directory to hold the "charts" (if it doesn't already exist)
import errno
import os
try:
    os.makedirs("charts")
except OSError as exc:  # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir("charts"):
        pass
    else:
        raise

# Open file of known miner coinbase signatures and addresses
with open('known_miners.json') as file_object:
    miners = json.load(file_object) # return a dict

# Add counts, order, and color to the miners dictionary
for miner in miners:
    miners[miner]["count_period"] = 0 # The count for the current target adjustment period
    miners[miner]["count_total"] = 0  # The total count across all blocks
    miners[miner]["order"] = 1        # The order of appearance for each miner
    miners[miner]["color"] = (0,0,0) # The color for each miner

# Incrementing order of appearance for each miner
order = 1

# HSV Colors
spacing = 1.00 / len(miners) # evenly space color hues based on number of miners
hue = 0 # start hue at zero (red)

# Identify Miner
def identify(miners, ascii, scriptsig, address): # Takes miners dict, along with the current coinbase and address
    # Iterate over all the individual miners in the json file
    for miner in miners:

        # 1. Check the ascii coinbase signature to try and match a miner
        if "coinbase" in miners[miner]:
            miner_signature = miners[miner]["coinbase"] # array of possible signatures that each miner puts in the coinbase
            # See if the miner's signature is in the ascii format of the coinbase
            if any(x.encode("ascii") in ascii for x in miner_signature): # The strings read from the json file get read as unicode, so need to convert them to ascii strings
                return miner

        # 2. Check the hex coinbase signature to try and match a miner (if there is one)
        if "coinbase_hex" in miners[miner]:
            miner_signature_hex = miners[miner]["coinbase_hex"] # array of possible signatures that each miner puts in the coinbase
            # See if the miner's signature is in the ascii format of the coinbase
            if any(x.encode("ascii") in scriptsig for x in miner_signature_hex):
                return miner

        # 3. Check for the destination address of each miner (if there is one)
        if "address" in miners[miner]:
            miner_address = miners[miner]["address"]
            if any(x.encode("ascii") in address for x in miner_address):
                return miner

    # 4. Return Unknown if not found
    return "Unknown"


# Open file containing the block data (coinbase signatures and miner addresses for each block)
skip = True
with open('data/all.csv') as f:

    # height,time,bits,coinbase,address
    # 99994,1293622434,453281356,044c86041b020602,1C9ZsSXVajFXV44F1vhygu9ZLiNYJ2JLrc

    for line in f:
        # Skip the first line of the csv file (the header)
        if skip:
            skip = False
            continue

        # Grab each field
        fields = line.rstrip().split(",")
        height = fields[0]
        timestamp = fields[1]
        bits = fields[2]
        scriptsig = fields[3]
        address = fields[4]
        ascii = scriptsig.decode("hex") # [!] Does not work for Python 3

        # Set a variable to update if we have found a miner (used for counting Unknown miners)
        found = False

        # Identify the miner
        name = identify(miners, ascii, scriptsig, address)
        #print height, name, ascii # Check out the miners as we go to see if we've missed any

        # Add to counters
        miners[name]["count_period"] += 1 # If we've found a match, add to the counter for that miner
        miners[name]["count_total"] += 1 # If we've found a match, add to the counter for that miner

        # Set color and order for the miner if it has just appeared
        if miners[name]["count_total"] == 1:
            # Set color
            color = "#" + hashlib.sha256(name).hexdigest()[-7:-1] # set random color based on hash of color name
            # color = colorsys.hsv_to_rgb(hue, 0.8, 0.8) # set color moving across the hue spectrum
            hue += spacing  # update the hue for the next miner
            miners[name]["color"] = color

            # Set order of appearance (so that we can keep a miners position in the chart)
            miners[name]["order"] = order # starting at 1
            order += 1

        ######################################
        # Plot a chart after every 2016 blocks (at every difficulty adjustment, roughly every 2 weeks)
        ######################################
        if int(height) > 0 and int(height) % 2016 == 0:

            # Sort multidimensional miners dictionary (by order, to keep each miner in the same position on the pie chart)
            sorted_by_appearance = miners.items()
            sorted_by_appearance.sort(key=lambda x: x[1]['order'])

            # Create a list of labels and a list of values (for use in plotting the chart)
            labels = list()
            values = list()

            # Also create a dictionary of each miner's percentage of total blocks mined (for the legend)
            percentages = dict()
            totalblocks = 0
            for miner in miners:
                totalblocks += miners[miner]["count_period"]

            # Show final counts for all miners
            for item in sorted_by_appearance:
                # Only add miner to list if they have mined a block in this period
                if item[1]['count_period'] > 0:
                    labels.append(item[0])
                    values.append(item[1]['count_period'])
                    percentage = (float(item[1]['count_period']) / float(totalblocks)) * 100
                    percentages[item[0]] = "{0:.2f}".format(percentage) + "%" # save as 2 decimal places

            # Create the figure
            fig = plt.figure(figsize=[8, 8]) # module - contains plot elements 8 inches = 768px

            # Add plot to the figure
            ax = fig.add_subplot(111) # specify plot position on figure (e.g. grids = row/column/position, 221, 222, 223, 224)

            # Plot the pie chart in the figure, and grab the wedges from the plot
            wedges = ax.pie(values, labels=labels, labeldistance=1.05, startangle=90) # frame=True

            # Set the individual wedge colors (using colors in the miners dictionary)
            for wedge in wedges[0]:
                    wedge.set_edgecolor('white')
                    wedge.set_facecolor(miners[wedge.get_label()]["color"])

            ########
            # Legend - in order of number of blocks mined (need to reorder handles and labels)
            ########

            # Sort multidimensional miners dictionary (by count_period, the number of block mined during this period)
            sorted_by_count = miners.items()
            sorted_by_count.sort(key=lambda x: x[1]['count_period'], reverse=True)

            # Create a dict to hold the position of each miner based on number of blocks mined
            positions = dict()
            p = 0
            for item in sorted_by_count:
                # Only add miner to list if they have mined a block in this period
                if item[1]['count_period'] > 0:
                    positions[item[0]] = p  # miner:position
                    p += 1

            # get current handles and labels
            handles, labels = ax.get_legend_handles_labels()

            # empty lists to hold new order of handles and labels for the legend
            new_handles = [None] * len(handles) # empty list to hold new order of handles for the legend
            new_labels = [None] * len(handles)  # empty list to hold new order of labels for the legend

            # Iterate over current handles and labels to put them in a new order
            for i in range(len(handles)):
                minername = labels[i]
                # Use the positions dict to insert handles and labels in to position in the new lists
                new_handles[positions[minername]] = handles[i]
                new_labels[positions[minername]]  = labels[i] + ' ' + percentages[minername] # add % to label

            plt.legend(new_handles, new_labels, loc="upper left")

            # [ ] TODO: Place legend to the side of pie chart.

            # Add date to bottom right corner
            date = datetime.datetime.utcfromtimestamp(float(timestamp)).strftime('%d %b %Y')
            plt.text(1.25, -1, date, horizontalalignment='right', color='#333333', fontsize=20, fontname='Ubuntu Mono') # 1,-1 = right lower

            # Add block number to bottom left corner
            prettyheight = '{:,}'.format(int(height))
            plt.text(-1.25, -1, "Block: " + prettyheight, color='#333333', fontsize=20, fontname='Ubuntu Mono') # -1,-1 = left lower

            # Add title
            plt.title('Bitcoin Mining Distribution', fontsize=28, fontname='Ubuntu', pad=28)

            # Remove whitespace from around pie chart
            fig.tight_layout()

            # Change the axis properties so that every pie chart ends up being the same size (irrespective of labels)
            plt.axis('off') # equal, tight

            # Save figure to file
            datestring = datetime.datetime.utcfromtimestamp(float(timestamp)).strftime('%Y_%m_%d') # %Y_%m_%d__%H_%M_%S
            plt.savefig('charts/' + height.zfill(8) + '__' + datestring + '.png')
            #plt.show()

            # Clear the figure so we can plot a new chart afresh next time
            plt.clf()      # clear
            plt.close(fig) # close (memory leak otherwise!)

            # Show results in terminal
            print height
            print percentages

            # Reset the counts so we can create a fresh chart for the next target period
            for miner in miners:
                miners[miner]["count_period"] = 0

###############
# Final Results
###############

# Sort multidimensional miners dictionary (by count_total)
sorted_by_total_count = miners.items()
sorted_by_total_count.sort(key=lambda x: x[1]['count_total'], reverse=True)

print
for item in sorted_by_total_count:
    print item[0], item[1]['count_total']
