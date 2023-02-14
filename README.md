# JPTrainer
<p>
JPTrainer helps the user practice writing Japanese characters using a drawing pad in which characters are detected using an AI model. For more details on JPTrainer, check the overview linked below.
</p>

<h2>Index</h2>
<ul>
  <li><a href="#Overview">Overview</a></li>
  <li><a href="#HowtoUse">How to Use</a></li>
  <li><a href="#Controls">Controls</a></li>
</ul>

<h2 id="Overview">Overview</h2>
<p>
JPTrainer is a program built to help beginners of the Japanese language practice writing foreign characters. You can use it to learn any combination of Hiragana, Katakana, or Kanji characters. The current iteration of the program is limited to N5 Kanji due to a lack of clear data on higher-level Kanjis. More levels could be easily added by simply finding relevant training images and running the buildModel.py file.<br>

The user is given random characters from the chosen subset which have to be drawn and submitted using the provided canvas. An AI model will try to predict what the user is trying to draw in real-time displaying the current guess in a small window to the right of the canvas. There are separate models specialized in the different character collections (Hiragana, Katakana, and Kanji) which work together to better guess what the user has drawn. Using this decentralised collection of highly specialized models leads to a much higher prediction accuracy than using a single more general algorithm (~95% vs ~80% accuracy). Below is a short video of the program being used:
</p>
<img src="https://user-images.githubusercontent.com/116522220/218885380-5b80c268-653e-46ec-81b4-bb4ea47f9ada.gif">


<h2 id="HowtoUse">How to Use</h2>
<p>
To use the program you must first ensure that you have the necessary libraries. To install the missing ones, access the project folder using your console or IDE and run the following command: <br><br>
<b>pip install -r requirements.txt</b><br><br>
After installing the missing libraries, simply run the main.pyw file using python.<br>
If you want to rebuild the model or give it a different set of data, use the buildModel.py script in the model folder. Keep in mind that due to privacy concerns, the data used to build this model is not included, you can read more about this on the _IMPORTANT.txt file.
</p>


<h2 id="Controls">Controls</h2>
<p>
Main menu:<br>
<ul>
  <li>Select the set of characters that you want to train by clicking on them, colored sets are the ones that will be used.</li>
  <li>After you are happy with your selection, click on the "Start Studying" button to begin.</li>
</ul>

Training screen:<br>
<ul>
  <li>Draw on the canvas the character defined at the top right of the screen.</li>
  <li>Click on the brush or eraser button to change between the two</li>
  <li>Change the brush or eraser size by using the slider below the wipe button. The red circle around the mouse tells you the current size.</li>
  <li>Press the wipe button to clear the canvas</li>
  <li>See the correct/incorrect status of your responses at the top right of the screen</li>
  <li>Use the prediction ease slider to change how strict predictions are, increase it if you are having trouble with predictions.</li>
</ul>
</p>
