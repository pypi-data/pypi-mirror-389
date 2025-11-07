# #########################################################################################
# Build image with everything required to run local and remote HEROS
# #########################################################################################

FROM python:3-slim

# Copy the contents of the repository into the image
WORKDIR /git
COPY . heros

# Install HEROS in editable mode
RUN pip install --break-system-packages -e heros/ && \
    mkdir /git/custom && echo -e 'import sys\nsys.path.insert(0, "/git/custom")' > /usr/local/lib/`ls /usr/local/lib | grep -P ^python3\.[[:digit:]]+$`/site-packages/sitecustomize.py
