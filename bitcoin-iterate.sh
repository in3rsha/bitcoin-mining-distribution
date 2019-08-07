# Get the coinbase scriptsigs from every block in the blockchain.
# ---------------------------------------------------------------

# Check bitcoin-cli is working and get the current block count
if bitcoin-cli getblockcount 2> /dev/null; then
  BLOCKCOUNT=$(bitcoin-cli getblockcount | tr -d "\n")
  echo "Current block height: $BLOCKCOUNT"
else
  echo "Could not connect to bitcoin-cli. Is bitcoind running?"
  exit 1
fi

# Make a directory to hold all the intermediate data
mkdir -p data # -p: doesn't return an error if the directory already exists

# 1. Get block header data (height, timestamp, target)
echo "bitcoin-iterate (blocks headers) > data/blocks.txt"
bitcoin-iterate -q --block=%bN,%bs,%bt > data/blocks.txt

# 2. Get every coinbase transaction (takes about 40 mins - 300MB)
echo "bitcoin-iterate (coinbase transactions) > data/txs.txt"
bitcoin-iterate -q --transaction=%tN,%tX | grep "^0," | cut -d "," -f 2 > data/txs.txt

# 3. Decode the coinbase transactions to get the input scriptsig and first output address (65 mins - 80MB)
echo "Decoding coinbase transactions to get scriptsigs and addresses > data/txs_scriptsigs_addresses.txt"
rm -f txs_scriptsigs_addresses.txt # delete existing file so that we don't accidentally append to it
while read LINE; do bitcoin-cli decoderawtransaction "$LINE" | jq '"\(.vin[0].coinbase),\(.vout[0].scriptPubKey.addresses[0])"' | tr -d '"' >> data/txs_scriptsigs_addresses.txt; done < data/txs.txt

# 4. Truncate the files so that they're both the same length as block.txt
LENGTH=$(wc -l data/blocks.txt | cut -d" " -f1)
LENGTH=$((LENGTH+1)) # Add 1, because this line will get deleted in sed too
echo "Truncating data/blocks.txt, data/txs_scriptsigs_addresses.txt to $LENGTH lines."
sed -i "$LENGTH,$ d" data/blocks.txt     # -i.backup to create a backup
sed -i "$LENGTH,$ d" data/txs_scriptsigs_addresses.txt

# 5. Join the two files horizontally (gather all block/miner information in to one file)
echo "Combining files: data/blocks.txt data/txs_scriptsigs_addresses.txt > data/all.txt"
paste -d "," data/blocks.txt data/txs_scriptsigs_addresses.txt > data/all.txt

# 6. Add a header to the file and rename it to a csv file
echo "Renaming data/all.txt to data/all.csv"
sed -i '1s/^/height,time,bits,coinbase,address\n/' data/all.txt
mv data/all.txt data/all.csv

# 6. Cleanup temporary data files
echo "Deleting temporary files: data/blocks.txt, data/txs.txt, data/txs_scriptsigs_addresses.txt"
rm data/blocks.txt
rm data/txs.txt
rm data/txs_scriptsigs_addresses.txt
