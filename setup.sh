#!/bin/bash

# Create rawprint.sh
echo '#!/bin/bash
tempfile=$(mktemp)
cat > "$tempfile"
lp -d PDF -U pi "$tempfile"
rm "$tempfile"' > /usr/local/bin/rawprint.sh

# Make it executable
sudo chmod +x /usr/local/bin/rawprint.sh

# Create rawprint_server.sh
echo '#!/bin/bash
while true; do
  nc -l -p 9100 -e /usr/local/bin/rawprint.sh
done' > /usr/local/bin/rawprint_server.sh

# Make it executable
sudo chmod +x /usr/local/bin/rawprint_server.sh

# Add to /etc/rc.local for startup (ensure the ampersand `&` to run in the background)
sudo sed -i '$i /usr/local/bin/rawprint_server.sh &' /etc/rc.local
