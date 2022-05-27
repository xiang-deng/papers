cd /home/deng.595/workspace/papers
python /home/deng.595/workspace/papers/parse/gmail.py
cd /home/deng.595/workspace/papers/docs
rm -rf /home/deng.595/workspace/papers/docs/_site
rm -r /home/deng.595/workspace/papers/docs/feed.xml
bundle exec jekyll build
cp /home/deng.595/workspace/papers/docs/_site/feed.xml /home/deng.595/workspace/papers/docs/feed.xml
