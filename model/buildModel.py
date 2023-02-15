# Imports
import itertools
import numpy as npy
import tensorflow as tf
from matplotlib import pyplot as plt
from PIL import Image, ImageFilter
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Dropout, Flatten, MaxPooling2D
from keras import backend as back
from random import randint
from tensorflow import keras
import japanize_matplotlib
from sys import exit
import pickle
import os
import math

BUILD_MODEL = True

EPOCHS = 3
TRAINING_SPLIT = 0.8
INTERMEDIATE_LAYER = 800
PARALLELISM = 10

GENERATION_FACTOR = 6
MAX_MOVEMENT_FORCE = 5
MAX_SKEW_FORCE = 5

# Main function
def main():

    # Builds collection paths
    paths = joinDictionaries([*buildPaths()])
    trainImgs, trainLabels, testImgs, testLabels = handleData(paths)

    # Handles model creation
    if BUILD_MODEL:
        model = buildModel(max(trainLabels) + 1)
        model.fit(x = trainImgs, y = trainLabels, epochs = EPOCHS)
        model.save("build")

        # Evaluates model
        print("Testing model...")
        model.evaluate(testImgs, testLabels)
    else:
        print("Loading model...")
        model = keras.models.load_model("build")
    
    # Plots sample predictions
    print("\nBuilding plot predictions...")
    correctPredictions, incorrectPredictions = makePredictions(model, testImgs, testLabels)
    plotPredictions(correctPredictions, incorrectPredictions, testImgs)
    print()

# Plots set of correct and incorrect predictions
def plotPredictions(correctPredictions, incorrectPredictions, testImgs):

    characterMap = N5KANJI

    # Creates 4X6 graph
    fig, axes = plt.subplots(nrows=4, ncols=6, figsize=(12, 8))
    for row in range(len(axes)):
        for col in range(len(axes[row])):

            # Correct predictions
            if row < 2:
                prediction = correctPredictions.pop(0)
                character = characterMap[prediction[1]]
                axes[row][col].set_title(f"Correct - A({character})")
                
            # incorrect prediction
            else:
                prediction = incorrectPredictions.pop(0)
                characters = characterMap[prediction[1]], characterMap[prediction[2]]
                axes[row][col].set_title(f"Incorrect - P({characters[0]}):A({characters[1]})")

            # Removes axis and draws plot
            imgIndex = prediction[0]
            axes[row][col].imshow(testImgs[imgIndex].reshape(50, 50), cmap="Blues")
            axes[row][col].axis('off')

    fig.tight_layout()
    plt.show()

# Returns sample correct and incorrect predictions
def makePredictions(model, testImgs, testLabels):

    correctPredictions = []
    incorrectPredictions = []

    # Fetches set of 12 correctly predicted images
    while len(correctPredictions) < 12:
        imgIndex = randint(0, testImgs.shape[0])
        prediction = model.predict(testImgs[imgIndex].reshape(1, 50, 50, 1))
        if(prediction.argmax() == testLabels[imgIndex]):
            correctPredictions.append([imgIndex, prediction.argmax()])
    
    # Fetches set of 12 incorrectly predicted images
    while len(incorrectPredictions) < 12:
        imgIndex = randint(0, testImgs.shape[0])
        prediction = model.predict(testImgs[imgIndex].reshape(1, 50, 50, 1))
        if(prediction.argmax() != testLabels[imgIndex]):
            incorrectPredictions.append([imgIndex, prediction.argmax(), testLabels[imgIndex]])
    
    return correctPredictions, incorrectPredictions

# Creates used model
def buildModel(labelNum):

    # Generates model
    model = Sequential()
    model.add(Conv2D(50, kernel_size=(3, 3), input_shape = (50, 50, 1)))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Flatten())
    model.add(Dense(INTERMEDIATE_LAYER, activation=tf.nn.relu))
    model.add(Dropout(0.2))
    model.add(Dense(INTERMEDIATE_LAYER / 1.5, activation=tf.nn.relu))
    model.add(Dropout(0.2))
    model.add(Dense(INTERMEDIATE_LAYER / 2, activation=tf.nn.relu))
    model.add(Dropout(0.2))
    model.add(Dense(labelNum, activation=tf.nn.softmax))
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    return model

# Determines how to fetch model's data
def handleData(paths):

    # Loads data if it exists
    if os.path.exists("trainImgs.npy") and os.path.exists("trainLabels.npy") and \
    os.path.exists("testImgs.npy") and os.path.exists("testLabels.npy"):

        print("Loading data...")

        # Training data
        trainImgs = npy.load("trainImgs.npy")
        trainLabels = npy.load("trainLabels.npy")

        # Testing data
        testImgs = npy.load("testImgs.npy")
        testLabels = npy.load("testLabels.npy")

    # Builds data if it does not exist
    else:
        print("Building data...")
        trainImgs, trainLabels, testImgs, testLabels = generateData(paths)

    print()
    return trainImgs, trainLabels, testImgs, testLabels

# Generates data used to train the model
def generateData(paths):

    # Initializes data
    trainImgs = []
    testImgs = []
    trainLabels = []
    testLabels = []

    # Loops over characters and images
    # collection = HIRAGANA + KATAKANA + N5KANJI + N4KANJI + N3KANJI + N2KANJI + N1KANJI
    collection = N5KANJI
    imageCount = 0
    for characterNum, character in enumerate(collection):
        print(f"Generating {character} - {characterNum + 1:04}/{len(collection):04} " +\
        f"({(characterNum + 1)/len(collection) * 100:06.02f}%)")
        for folder in paths[character]:
            for imageName in os.listdir(folder)[1:]:

                # Loads and normalizes image
                imagePath = folder + f"\{imageName}"
                image = Image.open(imagePath, "r")
                image = image.filter(ImageFilter.GaussianBlur(radius=1))
                image = image.resize((50, 50))
                sharp = sharpenImage(image)

                # Generates random image permutations
                permutations = [sharp]
                for _ in range(GENERATION_FACTOR - 1):

                    xMovement = randint(-MAX_MOVEMENT_FORCE, MAX_MOVEMENT_FORCE)
                    yMovement = randint(-MAX_MOVEMENT_FORCE, MAX_MOVEMENT_FORCE)
                    moved = moveImage(sharp, xMovement, yMovement, 255)

                    skewForce = randint(-MAX_SKEW_FORCE, MAX_SKEW_FORCE)
                    skewed = sharpenImage(skewImage(moved, skewForce, 255, "EXTRA_SMOOTH"))
                    permutations.append(skewed)

                # Gets pixel data
                for permutation in permutations:

                    # Determines if image should be used for testing or training
                    target = "TEST"
                    if imageCount % 10 < TRAINING_SPLIT * 10:
                        target = "TRAIN"

                    imageData = npy.array(permutation.getdata()).reshape((*permutation.size, 1)) / 255

                    # Saves for training
                    if target == "TEST":
                        testImgs.append(imageData)
                        testLabels.append(characterNum)

                    elif target == "TRAIN":
                        trainImgs.append(imageData)
                        trainLabels.append(characterNum)
                    
                    imageCount += 1

    # Converts data to numpy
    trainImgs = npy.array(trainImgs)
    testImgs = npy.array(testImgs)
    trainLabels = npy.array(trainLabels)
    testLabels = npy.array(testLabels)

    # Saves fetched data
    npy.save("trainImgs", trainImgs)
    npy.save("trainLabels", trainLabels)
    npy.save("testImgs", testImgs)
    npy.save("testLabels", testLabels)

    # Returns finalized data
    return trainImgs, trainLabels, testImgs, testLabels

# Lossy noise reduction function
def sharpenImage(image):

    # Generates sharp edges image
    sharp = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    sharpData = sharp.load()

    # Finds average background noise
    noise = max(max(max(
        npy.average(sharp.crop((0, 0, 3, 3)).getdata()),
        npy.average(sharp.crop((46, 46, 49, 49)).getdata())),
        npy.average(sharp.crop((0, 46, 3, 49)).getdata())),
        npy.average(sharp.crop((46, 0, 49, 3)).getdata())
    )
    
    # Removes noise
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            if abs(sharpData[x, y] - noise) < 60: sharpData[x, y] = 255

    # Finalizes smooth letter rendering
    return sharp.filter(ImageFilter.SMOOTH)

# Moves image by given x and y
def moveImage(image, x, y, fillColor):

    width, height = image.size
    moved = Image.new('L', (width, height))
    movedData = moved.load()

    # loops over image
    for col in range(width):
        for row in range(height):

            # Moves pixel
            imagePixel = image.getpixel((col, row))
            newCol = col + x
            newRow = row + y

            # Attaches moved pixel
            if newCol >= 0 and newCol < width and newRow >= 0 and newRow < height:
                moved.putpixel((newCol, newRow), imagePixel)

            # Fills x movement
            if x > 0 and col < x:
                movedData[col, row] = fillColor
            if x < 0 and col >= width + x:
                movedData[col, row] = fillColor
            
            # Fills y movement
            if y > 0 and row < y:
                movedData[col, row] = fillColor
            if y < 0 and row >= height + y:
                movedData[col, row] = fillColor

    return moved

# Skews an image by the given intensity
def skewImage(image, intensity, fillColor, filtering="NONE"):

    # Generates new image to be returned
    width, height = image.size
    skewed = Image.new('L', (width, height))

    # Fetches pixel data
    imageData = image.load()
    skewedData = skewed.load()

    mapped = [[0 for col in range(width)] for row in range(height)]

    # loops over pixels
    for x, y in itertools.product(range(width), range(height)):

        # Get the new x and y
        newX = x + int(intensity * math.sin(2 * math.pi * y / (width * 1.25)))
        newY = y + int(intensity * math.cos(2 * math.pi * x / (height * 1.25)))

        if newX < width and newY < height:
            skewedData[newX, newY] = imageData[x, y]
            mapped[newY][newX] = 1
    
    for row in range(height):
        for col in range(width):
            if mapped[row][col] == 0:
                skewedData[col, row] = fillColor

    # Return the new image
    if filtering=="SMOOTH": skewed = skewed.filter(ImageFilter.SMOOTH)
    elif filtering=="EXTRA_SMOOTH": skewed = skewed.filter(ImageFilter.SMOOTH_MORE)
    return skewed

# Joins multiple dictionaries
def joinDictionaries(dictionaries):

    joined = {}
    for dictionary in dictionaries:
        joined.update(dictionary)
    return joined

# Determines paths to find
def buildPaths():

    # Finds hiragana paths
    print("Fetching hiragana paths...")
    if os.path.exists("paths/hiragana.path"):

        # Loads existing paths
        with open("paths/hiragana.path", "rb") as f:
            hiraganaPaths = pickle.load(f)
    else:

        # Saves fetched paths
        hiraganaPaths = findPaths(HIRAGANA)
        with open("paths/hiragana.path", "wb") as f:
            pickle.dump(hiraganaPaths, f)
    
    # Finds katakana paths
    print("Fetching katakana paths...")
    if os.path.exists("paths/katakana.path"):

        # Loads existing paths
        with open("paths/katakana.path", "rb") as f:
            katakanaPaths = pickle.load(f)
    else:

        # Saves fetched paths
        katakanaPaths = findPaths(KATAKANA)
        with open("paths/katakana.path", "wb") as f:
            pickle.dump(katakanaPaths, f)
    
    # Finds n5 kanji paths
    print("Fetching N5 kanji paths...")
    if os.path.exists("paths/n5kanji.path"):

        # Loads existing paths
        with open("paths/n5kanji.path", "rb") as f:
            n5kanjiPaths = pickle.load(f)
    else:

        # Saves fetched paths
        n5kanjiPaths = findPaths(N5KANJI)
        with open("paths/n5kanji.path", "wb") as f:
            pickle.dump(n5kanjiPaths, f)

    # Finds n4 kanji paths
    print("Fetching N4 kanji paths...")
    if os.path.exists("paths/n4kanji.path"):

        # Loads existing paths
        with open("paths/n4kanji.path", "rb") as f:
            n4kanjiPaths = pickle.load(f)
    else:

        # Saves fetched paths
        n4kanjiPaths = findPaths(N4KANJI)
        with open("paths/n4kanji.path", "wb") as f:
            pickle.dump(n4kanjiPaths, f)

    # Finds n3 kanji paths
    print("Fetching N3 kanji paths...")
    if os.path.exists("paths/n3kanji.path"):

        # Loads existing paths
        with open("paths/n3kanji.path", "rb") as f:
            n3kanjiPaths = pickle.load(f)
    else:

        # Saves fetched paths
        n3kanjiPaths = findPaths(N3KANJI)
        with open("paths/n3kanji.path", "wb") as f:
            pickle.dump(n3kanjiPaths, f)
    
    # Finds n2 kanji paths
    print("Fetching N2 kanji paths...")
    if os.path.exists("paths/n2kanji.path"):

        # Loads existing paths
        with open("paths/n2kanji.path", "rb") as f:
            n2kanjiPaths = pickle.load(f)
    else:

        # Saves fetched paths
        n2kanjiPaths = findPaths(N2KANJI)
        with open("paths/n2kanji.path", "wb") as f:
            pickle.dump(n2kanjiPaths, f)
    
    # Finds n1 kanji paths
    print("Fetching N1 kanji paths...")
    if os.path.exists("paths/n1kanji.path"):

        # Loads existing paths
        with open("paths/n1kanji.path", "rb") as f:
            n1kanjiPaths = pickle.load(f)
    else:

        # Saves fetched paths
        n1kanjiPaths = findPaths(N1KANJI)
        with open("paths/n1kanji.path", "wb") as f:
            pickle.dump(n1kanjiPaths, f)
        
    print()
    return hiraganaPaths, katakanaPaths, n5kanjiPaths, n4kanjiPaths, n3kanjiPaths, n2kanjiPaths, n1kanjiPaths

# Finds character paths
def findPaths(characterSet):

    # loops over characters
    collectionPaths = {}

    # Loops over collections
    for character in characterSet:
        for collection in os.listdir("images"):

            # Loops over characters in collection
            for char in os.listdir(f"images\{collection}"):
                with open(f"images\{collection}\{char}\.char.txt", "r", encoding="utf-8") as file:

                    # Determines if file holds character we are looking for
                    read = file.readline()
                    if read == character:
                        if character in collectionPaths:
                            collectionPaths[character].append(f"images\{collection}\{char}")
                        else: collectionPaths[character] = [f"images\{collection}\{char}"]

    # Returns collection of paths
    return collectionPaths

HIRAGANA_ALL = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ', 'が', 'ぎ', 'ぐ', 'げ', 'ご', 'さ', 'し', 'す',
'せ', 'そ', 'ざ', 'じ', 'ず', 'ぜ', 'ぞ', 'た', 'ち', 'つ', 'て', 'と', 'だ', 'ぢ', 'づ', 'で', 'ど', 'な', 'に', 'ぬ',
'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ば', 'び', 'ぶ', 'べ', 'ぼ', 'ぱ', 'ぴ', 'ぷ', 'ぺ', 'ぽ', 'ま', 'み', 'む',
'め', 'も', 'や', 'ゆ', 'よ', 'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'を', 'ん']

KATAKANA_ALL = ['ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ', 'コ', 'ガ', 'ギ', 'グ', 'ゲ', 'ゴ', 'サ', 'シ', 'ス',
'セ', 'ソ', 'ザ', 'ジ', 'ズ', 'ゼ', 'ゾ', 'タ', 'チ', 'ツ', 'テ', 'ト', 'ダ', 'ヂ', 'ヅ', 'デ', 'ド', 'ナ', 'ニ', 'ヌ',
'ネ', 'ノ', 'ハ', 'ヒ', 'フ', 'ヘ', 'ホ', 'バ', 'ビ', 'ブ', 'ベ', 'ボ', 'パ', 'ピ', 'プ', 'ペ', 'ポ', 'マ', 'ミ', 'ム',
'メ', 'モ', 'ヤ', 'ユ', 'ヨ', 'ラ', 'リ', 'ル', 'レ', 'ロ', 'ワ', 'ヲ', 'ン']

KANA_MAP_ALL = ['a', 'i', 'u', 'e', 'o', 'ka', 'ki', 'ku', 'ke', 'ko', 'ga', 'gi', 'gu', 'ge', 'go', 'sa', 'shi', 'su',
'se', 'so', 'za', 'ji', 'zu', 'ze', 'zo', 'ta', 'chi', 'tsu', 'te', 'to', 'da', 'ji', 'zu', 'de', 'do', 'na', 'ni',
'nu', 'ne', 'no', 'ha', 'hi', 'fu', 'he', 'ho', 'ba', 'bi', 'bu', 'be', 'bo', 'pa', 'pi', 'pu', 'pe', 'po', 'ma', 'mi',
'mu', 'me', 'mo', 'ya', 'yu', 'yo', 'ra', 'ri', 'ru', 're', 'ro', 'wa', 'wo', 'n/m']

HIRAGANA = ['あ', 'い', 'う', 'え', 'お', 'か', 'き', 'く', 'け', 'こ', 'さ', 'し', 'す', 'せ', 'そ', 'た', 'ち', 'つ',
'て', 'と', 'な', 'に', 'ぬ', 'ね', 'の', 'は', 'ひ', 'ふ', 'へ', 'ほ', 'ま', 'み', 'む', 'め', 'も', 'や', 'ゆ', 'よ',
'ら', 'り', 'る', 'れ', 'ろ', 'わ', 'を', 'ん']

KATAKANA = ['ア', 'イ', 'ウ', 'エ', 'オ', 'カ', 'キ', 'ク', 'ケ', 'コ', 'サ', 'シ', 'ス', 'セ', 'ソ', 'タ', 'チ', 'ツ',
'テ', 'ト', 'ナ', 'ニ', 'ヌ', 'ネ', 'ノ', 'ハ', 'ヒ', 'フ', 'ヘ', 'ホ', 'マ', 'ミ', 'ム', 'メ', 'モ', 'ヤ', 'ユ', 'ヨ',
'ラ', 'リ', 'ル', 'レ', 'ロ', 'ワ', 'ヲ', 'ン']

KANA_MAP = ['a', 'i', 'u', 'e', 'o', 'ka', 'ki', 'ku', 'ke', 'ko', 'sa', 'shi', 'su', 'se', 'so', 'ta', 'chi', 'tsu',
'te', 'to', 'na', 'ni', 'nu', 'ne', 'no', 'ha', 'hi', 'fu', 'he', 'ho', 'ma', 'mi', 'mu', 'me', 'mo', 'ya', 'yu', 'yo',
'ra', 'ri', 'ru', 're', 'ro', 'wa', 'wo', 'n/m']

N5KANJI = ['一', '七', '万', '三', '上', '下', '中', '九', '二', '五', '人', '今', '休', '何', '先', '入', '八', '六',
'円', '出', '分', '前', '北', '十', '千', '午', '半', '南', '友', '右', '名', '四', '国', '土', '外', '大', '天', '女',
'子', '学', '小', '山', '川', '左', '年', '後', '日', '時', '書', '月', '木', '本', '来', '東', '校', '母', '毎', '気',
'水', '火', '父', '生', '男', '白', '百', '聞', '行', '西', '見', '話', '語', '読', '車', '金', '長', '間', '雨', '電',
'食', '高']

N5KANJI_MAP = ['One', 'Seven', 'Ten Thousand', 'Three', 'Above, Up, Over', 'Below, Down, Under, Beneath',
'Middle, In, Inside, Center', 'Nine', 'Two', 'Five', 'Person', 'Now', 'Rest', 'What', 'Previous, Ahead, Past, Former',
'Enter', 'Eight', 'Six', 'Yen, Round, Circle', 'Exit', 'Part, Minute, Separate, Understand', 'Front, Before', 'North',
'Ten', 'Thousand', 'Noon', 'Half', 'South', 'Friend', 'Right', 'Name, Famous', 'Four', 'Country',
'Dirt, Soil, Earth, Ground', 'Outside', 'Big, Large', 'Heaven', 'Woman', 'Child, Kid', 'Study, Learn, Learning',
'Small, Little', 'Mountain', 'River', 'Left', 'Year', 'Behind, After, Back, Rear', 'Sun, Day', 'Time, Hour',
'Write, Writing', 'Moon, Month', 'Tree, Wood', 'Book, Origin, Real, Main', 'Come, Next', 'East', 'School',
'Mother, Mom, Mum', 'Every', 'Energy, Spirit', 'Water', 'Fire', 'Father, Dad', 'Life', 'Man', 'White', 'Hundred',
'Hear', 'Go', 'West', 'See', 'Talk, Speak', 'Language', 'Read', 'Car', 'Gold', 'Long, Leader',
'Interval, Interval Of Time, Time Interval', 'Rain', 'Electricity', 'Eat, Meal', 'Tall, Expensive, High']

N4KANJI = ['不', '世', '主', '事', '京', '仕', '代', '以', '会', '住', '体', '作', '使', '借', '元', '兄', '公', '写',
'冬', '切', '別', '力', '勉', '動', '医', '去', '口', '古', '台', '同', '味', '品', '員', '問', '図', '地', '堂', '場',
'売', '夏', '夕', '多', '夜', '妹', '姉', '始', '字', '安', '室', '家', '少', '屋', '工', '帰', '広', '店', '度', '建',
'弟', '強', '待', '心', '思', '急', '悪', '意', '手', '持', '教', '文', '料', '新', '方', '旅', '族', '早', '明', '映',
'春', '昼', '曜', '有', '服', '朝', '業', '楽', '歌', '止', '正', '歩', '死', '注', '洋', '海', '漢', '牛', '物', '特',
'犬', '理', '用', '田', '町', '画', '界', '病', '発', '的', '目', '真', '着', '知', '研', '社', '私', '秋', '究', '空',
'立', '答', '紙', '終', '習', '考', '者', '肉', '自', '色', '花', '英', '茶', '親', '言', '計', '試', '買', '貸', '質',
'赤', '走', '起', '足', '転', '近', '送', '通', '週', '運', '道', '重', '野', '銀', '開', '院', '集', '青', '音', '題',
'風', '飯', '飲', '館', '駅', '験', '魚', '鳥', '黒']

N4KANJI_MAP = ['Not', 'World, Generation', 'Master, Main', 'Action, Matter, Thing', 'Capital', 'Doing, Do',
'Substitute, Replace, Period, Age', 'From, Since, Compared With, With, By Means Of', 'Meet', 'Dwelling, Reside, Dwell',
'Body', 'Make', 'Use', 'Borrow', 'Origin', 'Older Brother, Big Brother, Elder Brother', 'Public', 'Copy', 'Winter',
'Cut', 'Separate', 'Power, Strength', 'Exertion', 'Move', 'Medicine', 'Past', 'Mouth', 'Old', 'Machine', 'Same',
'Flavor, Taste', 'Product, Article, Goods, Products', 'Member', 'Problem', 'Diagram', 'Earth, Ground',
'Hall, Public Chamber', 'Location, Place', 'Sell', 'Summer', 'Evening', 'Many, Much, Lots Of', 'Night, Evening',
'Younger Sister, Little Sister', 'Older Sister, Big Sister, Elder Sister', 'Begin, Start', 'Letter, Character, Symbol',
'Relax, Cheap', 'Room', 'House, Home', 'Few, A Little', 'Roof, Shop, Store', 'Construction, Industry',
'Return, Return Home', 'Wide', 'Shop, Store', 'Degrees, Occurrence', 'Build, Construct',
'Younger Brother, Little Brother', 'Strong, Strength', 'Wait', 'Heart', 'Think, Thought', 'Hurry', 'Bad, Evil', 'Idea',
'Hand', 'Hold', 'Teach', 'Writing, Sentence', 'Fee, Material', 'New', 'Direction, Way', 'Trip, Travel', 'Tribe, Family',
'Early, Fast, Quick', 'Bright', 'Reflect, Reflection', 'Spring', 'Noon', 'Weekday, Day Of The Week', 'Have',
'Clothes, Clothing', 'Morning', 'Business', 'Comfort, Ease, Pleasure', 'Song, Sing', 'Stop', 'Correct', 'Walk', 'Death',
'Pour', 'Western Style, Ocean', 'Sea, Ocean', 'Chinese, China', 'Cow', 'Thing', 'Special', 'Dog', 'Reason', 'Task, Use',
'Rice Paddy, Rice Field, Field', 'Town', 'Drawing, Picture, Painting', 'World', 'Sick, Sickness, Ill, Illness',
'Departure', 'Target, Al, ~Al, Like, ~Like', 'Eye', 'Reality', 'Wear, Arrive', 'Know', 'Sharpen', 'Company',
'I, Private', 'Autumn, Fall', 'Research', 'Sky', 'Stand', 'Answer, Response, Reply', 'Paper', 'End, Finish', 'Learn',
'Think, Consider', 'Someone, Somebody', 'Meat', 'Self', 'Color', 'Flower', 'England, English', 'Tea', 'Parent', 'Say',
'Measure, Measurement', 'Try, Attempt', 'Buy', 'Lend', 'Quality', 'Red', 'Run', 'Wake Up', 'Foot, Leg, Sufficient',
'Revolve', 'Near, Close', 'Send', 'Pass Through', 'Week', 'Carry, Luck', 'Road, Street, Path, Way', 'Heavy', 'Field',
'Silver', 'Open', 'Institution', 'Collect, Gather', 'Blue', 'Sound', 'Topic', 'Wind, Style', 'Meal, Food', 'Drink',
'Public Building', 'Station, Train Station', 'Test', 'Fish', 'Bird', 'Black']

N3KANJI = ['与', '両', '乗', '予', '争', '互', '亡', '交', '他', '付', '件', '任', '伝', '似', '位', '余', '例', '供',
'便', '係', '信', '倒', '候', '値', '偉', '側', '偶', '備', '働', '優', '光', '全', '共', '具', '内', '冷', '処', '列',
'初', '判', '利', '到', '制', '刻', '割', '加', '助', '努', '労', '務', '勝', '勤', '化', '単', '危', '原', '参', '反',
'収', '取', '受', '可', '号', '合', '向', '君', '否', '吸', '吹', '告', '呼', '命', '和', '商', '喜', '回', '因', '困',
'園', '在', '報', '増', '声', '変', '夢', '太', '夫', '失', '好', '妻', '娘', '婚', '婦', '存', '宅', '守', '完', '官',
'定', '実', '客', '害', '容', '宿', '寄', '富', '寒', '寝', '察', '対', '局', '居', '差', '市', '師', '席', '常', '平',
'幸', '幾', '座', '庭', '式', '引', '当', '形', '役', '彼', '徒', '得', '御', '必', '忘', '忙', '念', '怒', '怖', '性',
'恐', '恥', '息', '悲', '情', '想', '愛', '感', '慣', '成', '戦', '戻', '所', '才', '打', '払', '投', '折', '抜', '抱',
'押', '招', '指', '捕', '掛', '探', '支', '放', '政', '敗', '散', '数', '断', '易', '昔', '昨', '晩', '景', '晴', '暗',
'暮', '曲', '更', '最', '望', '期', '未', '末', '束', '杯', '果', '格', '構', '様', '権', '横', '機', '欠', '次', '欲',
'歯', '歳', '残', '段', '殺', '民', '求', '決', '治', '法', '泳', '洗', '活', '流', '浮', '消', '深', '済', '渡', '港',
'満', '演', '点', '然', '煙', '熱', '犯', '状', '猫', '王', '現', '球', '産', '由', '申', '留', '番', '疑', '疲', '痛',
'登', '皆', '盗', '直', '相', '眠', '石', '破', '確', '示', '礼', '祖', '神', '福', '科', '程', '種', '積', '突', '窓',
'笑', '等', '箱', '米', '精', '約', '組', '経', '給', '絵', '絶', '続', '緒', '罪', '置', '美', '老', '耳', '職', '育',
'背', '能', '腹', '舞', '船', '良', '若', '苦', '草', '落', '葉', '薬', '術', '表', '要', '規', '覚', '観', '解', '記',
'訪', '許', '認', '誤', '説', '調', '談', '論', '識', '警', '議', '負', '財', '貧', '責', '費', '資', '賛', '越', '路',
'身', '辞', '込', '迎', '返', '迷', '追', '退', '逃', '途', '速', '連', '進', '遅', '遊', '過', '達', '違', '遠', '適',
'選', '部', '都', '配', '酒', '閉', '関', '阪', '降', '限', '除', '険', '陽', '際', '雑', '難', '雪', '静', '非', '面',
'靴', '頂', '頭', '頼', '顔', '願', '類', '飛', '首', '馬', '髪', '鳴']

N3KANJI_MAP = ['Give', 'Both', 'Ride', 'Beforehand', 'Conflict', 'Mutual', 'Death, Deceased', 'Mix, Mingle', 'Other',
'Attach', 'Matter, Affair', 'Duty', 'Transmit, Tell', 'Resemble', 'Rank', 'Surplus, Excess', 'Example',
'Servant, Companion', 'Convenience, Convenient', 'Connection', 'Believe, Trust', 'Overthrow, Collapse',
'Climate, Weather, Candidate', 'Value, Price', 'Greatness', 'Side', 'Accidentally', 'Provide, Equip', 'Work, Labor',
'Superior, Gentle', 'Sunlight, Light', 'All, Whole', 'Together', 'Tool', 'Inside, Within', 'Cool, Cold', 'Deal With',
'Row', 'First', 'Judge', 'Profit, Benefit, Advantage', 'Arrival', 'Control, System', 'Carve', 'Divide', 'Add', 'Help',
'Toil', 'Labor', 'Task', 'Win', 'Work', 'Change', 'Simple', 'Dangerous', 'Original, Fundamental, Field', 'Participate',
'Anti', 'Obtain', 'Take', 'Accept, Receive', 'Possible, Passable', 'Number', 'Suit, Fit, Join', 'Yonder, Facing',
'Buddy', 'No', 'Suck, Inhale', 'Blow', 'Announce', 'Call', 'Fate', 'Peace, Japanese Style', 'Merchandise',
'Rejoice, Delighted, Pleased', 'Times, Revolve', 'Cause', 'Distressed, Troubled', 'Garden, Park', 'Exist',
'News, Report', 'Increase', 'Voice', 'Change, Strange', 'Dream', 'Fat', 'Husband', 'Fault', 'Like', 'Wife', 'Daughter',
'Marriage', 'Wife', 'Exist, Suppose', 'House, Home', 'Protect', 'Perfect', 'Government', 'Determine', 'Truth, Reality',
'Guest, Customer', 'Damage, Injury, Harm', 'Form, Appearance, Shape, Figure', 'Lodge', 'Approach', 'Rich', 'Cold',
'Lie Down, Lay Down, Sleep', 'Guess', 'Versus, Opposite', 'Bureau, Department', 'Alive', 'Distinction', 'City',
'Teacher, Expert, Master', 'Seat', 'Ordinary, Normal, Usual', 'Flat, Peace', 'Happiness', 'How Many, How Much',
'Sit, Seat', 'Garden', 'Ritual, Ceremony, Equation', 'Pull', 'Correct, Right, Success', 'Shape, Form, Appearance',
'Service, Duty', 'He', 'Junior, Follower', 'Acquire', 'Honorable', 'Certain', 'Forget', 'Busy', 'Thought',
'Angry, Anger', 'Scary', 'Gender, Nature, Sex', 'Fear', 'Shame', 'Breath', 'Sad', 'Feeling, Emotion', 'Concept', 'Love',
'Feeling', 'Accustomed', 'Become', 'War, Battle', 'Return', 'Place', 'Genius', 'Hit', 'Pay', 'Throw', 'Fold, Bend',
'Extract', 'Hug', 'Push', 'Beckon', 'Finger', 'Catch', 'Hang', 'Look For, Search For', 'Support, Branch', 'Release',
'Politics, Government', 'Failure, Fail', 'Scatter', 'Count, Number, Amount', 'Cut Off', 'Easy',
'Long Ago, Long Time Ago', 'Previous, Yesterday', 'Night, Evening', 'Scene', 'Clear Up', 'Dark', 'Livelihood',
'Music, Bend', 'Again, Renew', 'Most', 'Hope', 'Period Of Time, Time Period', 'Not Yet', 'End', 'Bundle',
'Cup Of Liquid, Counter For Cups', 'Fruit', 'Status', 'Set Up, Care', 'Formal Name Title, Formal Name Ender, Manner',
'Rights', 'Side, Horizontal', 'Machine', 'Lack', 'Next', 'Want', 'Tooth, Teeth', 'Years Old', 'Remainder',
'Steps, Stairs', 'Kill', 'Peoples, People, Nation', 'Request', 'Decide, Decision', 'Cure, Heal, Reign, Rule',
'Method, Law', 'Swim', 'Wash', 'Lively', 'Stream', 'Float', 'Extinguish', 'Deep', 'Come To An End', 'Transit',
'Harbor, Port, Harbour', 'Full', 'Perform, Performance', 'Point, Decimal, Decimal Point', 'Nature', 'Smoke',
'Heat, Fever', 'Crime', 'Condition', 'Cat', 'King', 'Present Time, Present', 'Sphere, Ball', 'Give Birth, Birth',
'Reason', 'Say Humbly, Say, Humbly Say', 'Detain', 'Number In A Series, Turn, Ordinal Number', 'Doubt', 'Exhausted',
'Pain', 'Climb', 'All, Everyone, Everything, Everybody', 'Steal', 'Fix, Direct', 'Mutual', 'Sleep', 'Stone', 'Tear',
'Certain', 'Indicate, Show', 'Thanks', 'Ancestor', 'God', 'Luck, Fortune', 'Course, Science, Department', 'Extent',
'Kind, Type', 'Accumulate', 'Stab, Thrust', 'Window', 'Laugh', 'Equal', 'Box', 'Rice, America', 'Spirit', 'Promise',
'Group, Association, Team', 'Passage of Time, Pass Through, Manage', 'Salary', 'Drawing, Painting',
'Extinction, Die Out', 'Continue', 'Together', 'Guilt', 'Put', 'Beauty, Beautiful', 'Elderly', 'Ear, Ears',
'Employment', 'Nurture, Raise', 'Back, Height', 'Ability', 'Belly, Abdomen, Stomach', 'Dance', 'Boat, Ship', 'Good',
'Young', 'Suffering', 'Grass, Weed', 'Fall', 'Leaf, Leaves', 'Medicine, Drug, Drugs', 'Art', 'Express', 'Need',
'Standard', 'Memorize, Awake', 'View', 'Untie, Solve', 'Write Down, Record', 'Visit', 'Permit, Allow', 'Recognize',
'Mistake', 'Theory', 'Investigate, Tone', 'Discuss', 'Theory', 'Discerning, Discriminating, Know', 'Warn, Admonish',
'Deliberation, Discussion', 'Lose', 'Wealth', 'Poor', 'Blame', 'Expense, Cost', 'Resources', 'Agree', 'Go Beyond',
'Road', 'Somebody, Someone, Body', 'Quit, Word', 'Crowded', 'Welcome', 'Return', 'Astray, Lost', 'Follow, Chase',
'Retreat, Reject', 'Escape', 'Route', 'Fast', 'Take Along', 'Advance', 'Slow', 'Play', 'Surpass', 'Attain, Plural',
'Different', 'Far', 'Suitable', 'Choose', 'Part, Department, Club', 'Metropolis', 'Distribute', 'Alcohol',
'Closed, Close, Closure', 'Related, Connected', 'Heights, Slope', 'Descend', 'Limit', 'Exclude, Remove', 'Risky, Steep',
'Sunshine, Sunlight', 'Occasion', 'Random, Miscellaneous', 'Difficult', 'Snow', 'Quiet', 'Injustice, Negative, Mistake',
'Face, Surface', 'Shoes', 'Summit, Humbly', 'Head', 'Trust', 'Face', 'Request', 'Type, Category, Kind', 'Fly', 'Neck',
'Horse', 'Hair', 'Chirp']

N2KANJI = ['並', '丸', '久', '乱', '乳', '乾', '了', '介', '仏', '令', '仲', '伸', '伺', '低', '依', '個', '倍', '停',
'傾', '像', '億', '兆', '児', '党', '兵', '冊', '再', '凍', '刊', '刷', '券', '刺', '則', '副', '劇', '効', '勇', '募',
'勢', '包', '匹', '区', '卒', '協', '占', '印', '卵', '厚', '双', '叫', '召', '史', '各', '含', '周', '咲', '喫', '営',
'団', '囲', '固', '圧', '坂', '均', '型', '埋', '城', '域', '塔', '塗', '塩', '境', '央', '奥', '姓', '委', '季', '孫',
'宇', '宝', '寺', '封', '専', '将', '尊', '導', '届', '層', '岩', '岸', '島', '州', '巨', '巻', '布', '希', '帯', '帽',
'幅', '干', '幼', '庁', '床', '底', '府', '庫', '延', '弱', '律', '復', '快', '恋', '患', '悩', '憎', '戸', '承', '技',
'担', '拝', '拾', '挟', '捜', '捨', '掃', '掘', '採', '接', '換', '損', '改', '敬', '旧', '昇', '星', '普', '暴', '曇',
'替', '札', '机', '材', '村', '板', '林', '枚', '枝', '枯', '柔', '柱', '査', '栄', '根', '械', '棒', '森', '植', '極',
'橋', '欧', '武', '歴', '殿', '毒', '比', '毛', '氷', '永', '汗', '汚', '池', '沈', '河', '沸', '油', '況', '泉', '泊',
'波', '泥', '浅', '浴', '涙', '液', '涼', '混', '清', '減', '温', '測', '湖', '湯', '湾', '湿', '準', '溶', '滴', '漁',
'濃', '濯', '灯', '灰', '炭', '無', '焼', '照', '燃', '燥', '爆', '片', '版', '玉', '珍', '瓶', '甘', '畜', '略', '畳',
'療', '皮', '皿', '省', '県', '短', '砂', '硬', '磨', '祈', '祝', '祭', '禁', '秒', '移', '税', '章', '童', '競', '竹',
'符', '筆', '筒', '算', '管', '築', '簡', '籍', '粉', '粒', '糸', '紅', '純', '細', '紹', '絡', '綿', '総', '緑', '線',
'編', '練', '績', '缶', '署', '群', '羽', '翌', '耕', '肌', '肩', '肯', '胃', '胸', '脂', '脳', '腕', '腰', '膚', '臓',
'臣', '舟', '航', '般', '芸', '荒', '荷', '菓', '菜', '著', '蒸', '蔵', '薄', '虫', '血', '衣', '袋', '被', '装', '裏',
'補', '複', '角', '触', '訓', '設', '詞', '詰', '誌', '課', '諸', '講', '谷', '豊', '象', '貝', '貨', '販', '貯', '貿',
'賞', '賢', '贈', '超', '跡', '踊', '軍', '軒', '軟', '軽', '輪', '輸', '辛', '農', '辺', '述', '逆', '造', '郊', '郵',
'量', '針', '鈍', '鉄', '鉱', '銅', '鋭', '録', '門', '防', '陸', '隅', '階', '隻', '雇', '雲', '零', '震', '革', '順',
'預', '領', '額', '香', '駐', '骨', '麦', '黄', '鼻', '齢']

N2KANJI_MAP = ['Line Up', 'Circle, Circular, Round', 'Long Time', 'Riot', 'Milk', 'Dry', 'Finish, Complete, End',
'Jammed In', 'Buddha', 'Orders', 'Relationship', 'Stretch', 'Pay Respects', 'Low', 'Reliant, Dependent', 'Individual',
'Double, Times, Multiply', 'Halt', 'Lean', 'Statue, Image', 'Hundred Million', 'Omen', 'Child', 'Party, Group',
'Soldier', 'Book Counter, Counter For Books, Counter For Volumes', 'Again', 'Frozen', 'Edition', 'Printing', 'Ticket',
'Stab', 'Rule', 'Vice, Side', 'Drama', 'Effective', 'Courage, Bravery, Valor, Valour', 'Recruit', 'Force', 'Wrap',
'Small Animal, Small Animal Counter', 'District, Ward', 'Graduate', 'Cooperation', 'Fortune, Occupy', 'Seal, Mark',
'Egg', 'Thick', 'Pair', 'Shout', 'Call, Eat', 'History', 'Each', 'Include', 'Circumference', 'Blossom', 'Consume',
'Manage', 'Group', 'Surround', 'Hard', 'Pressure', 'Slope', 'Equal', 'Model, Type', 'Bury', 'Castle',
'Region, Boundary', 'Tower', 'Paint', 'Salt', 'Boundary', 'Center, Centre', 'Interior', 'Surname, Family Name',
'Committee', 'Seasons', 'Grandchild', 'Outer Space', 'Treasure', 'Temple', 'Seal, Seal In, Closing', 'Specialty',
'Commander', 'Revered', 'Lead', 'Deliver', 'Layer', 'Boulder', 'Coast, Shore', 'Island', 'State, Province, County',
'Giant', 'Scroll', 'Cloth', 'Wish', 'Belt', 'Hat', 'Width', 'Dry', 'Infancy, Childhood', 'Agency, Government Office',
'Floor, Bed', 'Bottom', 'Government', 'Storage, Warehouse', 'Prolong', 'Weak', 'Law', 'Restore', 'Pleasant', 'Romance',
'Afflicted', 'Worry', 'Hate', 'Door', 'Consent', 'Skill', 'Carry, Bear', 'Worship', 'Pick Up', 'Between', 'Search',
'Throw Away', 'Sweep', 'Dig', 'Gather', 'Adjoin', 'Exchange', 'Loss', 'Renew', 'Respect', 'Former', 'Ascend', 'Star',
'Normal', 'Violence', 'Cloudy', 'Replace, Exchange', 'Bill, Tag, Label, Note', 'Desk', 'Lumber, Material, Timber',
'Village', 'Board', 'Forest, Woods', 'Flat Objects Counter, Flat Object, Counter For Flat Objects', 'Branch', 'Wither',
'Gentle', 'Pillar', 'Inspect, Investigate, Inspection, Investigation', 'Prosper, Flourish', 'Root', 'Contraption',
'Pole, Rod, Wooden Pole', 'Forest, Woods', 'Plant', 'Extreme', 'Bridge', 'Europe', 'Military', 'Continuation',
'Milord, Lord', 'Poison', 'Compare', 'Fur, Hair', 'Ice', 'Eternity', 'Sweat', 'Dirty', 'Pond', 'Sink', 'River', 'Boil',
'Oil', 'Condition', 'Spring, Fountain', 'Overnight', 'Wave', 'Mud', 'Shallow', 'Bathe', 'Teardrop', 'Fluid, Liquid',
'Cool', 'Mix', 'Pure', 'Decrease', 'Warm', 'Measure', 'Lake', 'Hot Water', 'Gulf', 'Damp', 'Standard', 'Melt', 'Drip',
'Fishing', 'Thick', 'Wash', 'Lamp', 'Ashes', 'Charcoal', 'Nothing', 'Bake, Cook, Burn', 'Illuminate', 'Burn', 'Dry Up',
'Explode', 'One Sided', 'Edition', 'Ball', 'Rare', 'Bottle, Jar', 'Sweet', 'Livestock', 'Abbreviation, Abbreviate',
'Tatami Mat', 'Heal', 'Skin', 'Plate, Dish', 'Conserve', 'Prefecture', 'Short', 'Sand', 'Stiff', 'Polish', 'Pray',
'Celebrate', 'Festival', 'Prohibit, Prohibition', 'Second', 'Shift', 'Tax', 'Chapter', 'Juvenile', 'Compete', 'Bamboo',
'Token', 'Writing Brush', 'Cylinder', 'Calculate, Calculation', 'Pipe', 'Construct, Build', 'Simplicity', 'Enroll',
'Powder', 'Grains', 'Thread', 'Deep Red, Crimson', 'Pure', 'Thin', 'Introduce', 'Entangle, Coil Around, Entwine',
'Cotton', 'Whole', 'Green', 'Line', 'Knit', 'Practice', 'Exploits', 'Can, Tin Can',
'Government Office, Political Office, Office', 'Flock', 'Feather, Feathers, Wing, Wings',
'The Following, Following, Next', 'Plow', 'Skin', 'Shoulder', 'Agreement, Consent', 'Stomach', 'Chest, Breast', 'Fat',
'Brain', 'Arm', 'Waist', 'Skin', 'Internal Organs', 'Servant, Retainer', 'Boat', 'Navigation', 'Generally, General',
'Acting, Art', 'Wild', 'Luggage', 'Cake', 'Vegetable', 'Author', 'Steam', 'Storehouse', 'Dilute', 'Insect, Bug',
'Blood', 'Clothes', 'Sack', 'Incur', 'Attire', 'Backside, Underside, Reverse', 'Supplement', 'Duplicate',
'Angle, Corner', 'Touch', 'Instruction', 'Establish',
'Part Of Speech, Speech Particle, Particle Of Speech, Grammar Particle', 'Stuffed', 'Magazine', 'Section', 'Various',
'Lecture', 'Valley', 'Plentiful', 'Elephant, Phenomenon', 'Shellfish, Shell', 'Freight', 'Sell', 'Savings', 'Trade',
'Prize', 'Clever', 'Presents', 'Ultra, Super', 'Traces', 'Dance', 'Army', 'House Counter, Eaves', 'Soft',
'Lightweight, Light, Light Weight', 'Wheel, Ring, Loop', 'Transport', 'Spicy', 'Farming, Agriculture', 'Area',
'Mention', 'Reverse, Opposite', 'Create', 'Suburbs', 'Mail', 'Quantity, Amount', 'Needle', 'Dull', 'Iron', 'Mineral',
'Copper', 'Sharp', 'Record', 'Gates, Gate', 'Prevent, Prevention', 'Land', 'Corner', 'Floor, Story, Storey',
'Ship Counter', 'Employ', 'Cloud', 'Zero, Spill', 'Earthquake, Quake, Shake', 'Leather', 'Order, Sequence', 'Deposit',
'Territory', 'Amount, Framed Picture, Forehead', 'Fragrance', 'Resident', 'Bone', 'Wheat', 'Yellow', 'Nose', 'Age']

N1KANJI_ALL = ['丁', '丑', '且', '丘', '丙', '丞', '丹', '乃', '之', '乏', '乙', '也', '亀', '井', '亘', '亜', '亥', '亦',
'亨', '享', '亭', '亮', '仁', '仙', '仮', '仰', '企', '伊', '伍', '伎', '伏', '伐', '伯', '伴', '伶', '伽', '但', '佐',
'佑', '佳', '併', '侃', '侍', '侑', '価', '侮', '侯', '侵', '促', '俊', '俗', '保', '修', '俳', '俵', '俸', '倉', '倖',
'倣', '倫', '倭', '倹', '偏', '健', '偲', '偵', '偽', '傍', '傑', '傘', '催', '債', '傷', '僕', '僚', '僧', '儀', '儒',
'償', '允', '充', '克', '免', '典', '兼', '冒', '冗', '冠', '冴', '冶', '准', '凌', '凜', '凝', '凡', '凪', '凱', '凶',
'凸', '凹', '刀', '刃', '刈', '刑', '削', '剖', '剛', '剣', '剤', '剰', '創', '功', '劣', '励', '劾', '勁', '勅', '勘',
'勧', '勲', '勺', '匁', '匠', '匡', '匿', '升', '卑', '卓', '博', '卯', '即', '却', '卸', '厄', '厘', '厳', '又', '及', 
'叔', '叙', '叡', '句', '只', '叶', '司', '吉', '后', '吏', '吐', '吟', '呂', '呈', '呉', '哀', '哉', '哲', '唄', '唆',
'唇', '唯', '唱', '啄', '啓', '善', '喚', '喝', '喪', '喬', '嗣', '嘆', '嘉', '嘱', '器', '噴', '嚇', '囚', '圏', '圭',
'坑', '坪', '垂', '垣', '執', '培', '基', '堀', '堅', '堕', '堤', '堪', '塀', '塁', '塊', '塑', '塚', '塾', '墓', '墜',
'墨', '墳', '墾', '壁', '壇', '壊', '壌', '士', '壮', '壱', '奇', '奈', '奉', '奎', '奏', '契', '奔', '奨', '奪', '奮',
'奴', '如', '妃', '妄', '妊', '妙', '妥', '妨', '姫', '姻', '姿', '威', '娠', '娯', '婆', '婿', '媒', '媛', '嫁', '嫌',
'嫡', '嬉', '嬢', '孔', '孝', '孟', '孤', '宏', '宗', '宙', '宜', '宣', '宥', '宮', '宰', '宴', '宵', '寂', '寅', '密',
'寛', '寡', '寧', '審', '寮', '寸', '射', '尉', '尋', '尚', '尭', '就', '尺', '尼', '尽', '尾', '尿', '屈', '展', '属',
'履', '屯', '岐', '岡', '岬', '岳', '峠', '峡', '峰', '峻', '崇', '崎', '崚', '崩', '嵐', '嵩', '嵯', '嶺', '巌', '巡',
'巣', '巧', '己', '巳', '巴', '巽', '帆', '帝', '帥', '帳', '幕', '幣', '幹', '幻', '幽', '庄', '序', '庶', '康', '庸',
'廃', '廉', '廊', '廷', '弁', '弊', '弐', '弓', '弔', '弘', '弥', '弦', '弧', '張', '弾', '彗', '彦', '彩', '彪', '彫',
'彬', '彰', '影', '往', '征', '径', '徐', '従', '循', '微', '徳', '徴', '徹', '忌', '忍', '志', '応', '忠', '怜', '怠',
'怪', '恒', '恕', '恨', '恩', '恭', '恵', '悌', '悔', '悟', '悠', '悦', '悼', '惇', '惑', '惜', '惟', '惣', '惨', '惰',
'愁', '愉', '愚', '慈', '態', '慎', '慕', '慢', '慧', '慨', '慮', '慰', '慶', '憂', '憤', '憧', '憩', '憲', '憶', '憾',
'懇', '懐', '懲', '懸', '我', '戒', '戯', '房', '扇', '扉', '扱', '扶', '批', '抄', '把', '抑', '抗', '択', '披', '抵',
'抹', '抽', '拍', '拐', '拒', '拓', '拘', '拙', '拠', '拡', '括', '拳', '拷', '挑', '挙', '振', '挿', '据', '捷', '捺',
'授', '掌', '排', '控', '推', '措', '掲', '描', '提', '揚', '握', '揮', '援', '揺', '搬', '搭', '携', '搾', '摂', '摘',
'摩', '撃', '撤', '撮', '撲', '擁', '操', '擦', '擬', '攻', '故', '敏', '救', '敢', '敦', '整', '敵', '敷', '斉', '斎',
'斐', '斗', '斜', '斤', '斥', '於', '施', '旋', '旗', '既', '旦', '旨', '旬', '旭', '旺', '昂', '昆', '昌', '昭', '是',
'昴', '晃', '晋', '晏', '晟', '晨', '晶', '智', '暁', '暇', '暉', '暑', '暖', '暢', '暦', '暫', '曙', '曹', '朋', '朔',
'朕', '朗', '朱', '朴', '朽', '杉', '李', '杏', '杜', '条', '松', '析', '枠', '枢', '架', '柄', '柊', '某', '染', '柚',
'柳', '柾', '栓', '栗', '栞', '株', '核', '栽', '桂', '桃', '案', '桐', '桑', '桜', '桟', '梅', '梓', '梢', '梧', '梨',
'棄', '棋', '棚', '棟', '棺', '椋', '椎', '検', '椰', '椿', '楊', '楓', '楠', '楼', '概', '榛', '槙', '槻', '槽', '標',
'模', '樹', '樺', '橘', '檀', '欄', '欣', '欺', '欽', '款', '歓', '殉', '殊', '殖', '殴', '殻', '毅', '毬', '氏', '汁',
'汐', '江', '汰', '汽', '沖', '沙', '没', '沢', '沼', '沿', '泌', '泡', '泣', '泰', '洞', '津', '洪', '洲', '洵', '洸',
'派', '浄', '浜', '浦', '浩', '浪', '浸', '涯', '淑', '淡', '淳', '添', '渇', '渉', '渋', '渓', '渚', '渥', '渦', '湧',
'源', '溝', '滅', '滉', '滋', '滑', '滝', '滞', '漂', '漆', '漏', '漠', '漫', '漬', '漱', '漸', '潔', '潜', '潟', '潤',
'潮', '澄', '澪', '激', '濁', '濫', '瀬', '災', '炉', '炊', '炎', '為', '烈', '焦', '煩', '煮', '熊', '熙', '熟', '燎',
'燦', '燿', '爵', '爽', '爾', '牧', '牲', '犠', '狂', '狙', '狩', '独', '狭', '猛', '猟', '猪', '献', '猶', '猿', '獄',
'獣', '獲', '玄', '率', '玖', '玲', '珠', '班', '琉', '琢', '琳', '琴', '瑚', '瑛', '瑞', '瑠', '瑳', '瑶', '璃', '環',
'甚', '甫', '甲', '畔', '畝', '異', '疎', '疫', '疾', '症', '痘', '痢', '痴', '癒', '癖', '皇', '皐', '皓', '盆', '益',
'盛', '盟', '監', '盤', '盲', '盾', '眉', '看', '眸', '眺', '眼', '睡', '督', '睦', '瞬', '瞭', '瞳', '矛', '矢', '矯',
'砕', '砲', '硝', '硫', '碁', '碑', '碧', '碩', '磁', '磯', '礁', '礎', '祉', '祐', '祥', '票', '禄', '禅', '禍', '禎',
'秀', '秘', '租', '秦', '秩', '称', '稀', '稔', '稚', '稜', '稲', '稼', '稿', '穀', '穂', '穏', '穣', '穫', '穴', '窃',
'窒', '窮', '窯', '竜', '竣', '端', '笙', '笛', '第', '笹', '筋', '策', '箇', '節', '範', '篤', '簿', '粋', '粗', '粘',
'粛', '糖', '糧', '系', '糾', '紀', '紋', '納', '紗', '紘', '級', '紛', '素', '紡', '索', '紫', '紬', '累', '紳', '紺',
'絃', '結', '絞', '絢', '統', '絹', '継', '綜', '維', '綱', '網', '綸', '綺', '綾', '緊', '緋', '締', '緩', '緯', '縁',
'縄', '縛', '縦', '縫', '縮', '繁', '繊', '織', '繕', '繭', '繰', '罰', '罷', '羅', '羊', '義', '翁', '翔', '翠', '翻',
'翼', '耀', '耐', '耗', '耶', '聖', '聡', '聴', '肇', '肖', '肝', '肢', '肥', '肪', '肺', '胆', '胎', '胞', '胡', '胤',
'胴', '脅', '脈', '脚', '脩', '脱', '脹', '腐', '腸', '膜', '膨', '臨', '臭', '至', '致', '興', '舌', '舎', '舗', '舜',
'舶', '艇', '艦', '艶', '芋', '芙', '芝', '芳', '芹', '芽', '苑', '苗', '茂', '茄', '茅', '茉', '茎', '茜', '荘', '莉',
'莞', '菊', '菌', '菖', '菫', '華', '萌', '萩', '葬', '葵', '蒔', '蒼', '蓄', '蓉', '蓮', '蔦', '蕉', '蕗', '薦', '薪',
'薫', '藍', '藤', '藩', '藻', '蘭', '虎', '虐', '虚', '虜', '虞', '虹', '蚊', '蚕', '蛇', '蛍', '蛮', '蝶', '融', '衆',
'街', '衛', '衝', '衡', '衰', '衷', '衿', '袈', '裁', '裂', '裕', '裟', '裸', '製', '褐', '褒', '襟', '襲', '覆', '覇',
'視', '覧', '訂', '討', '託', '訟', '訳', '訴', '診', '証', '詐', '詔', '評', '詠', '詢', '詩', '該', '詳', '誇', '誉',
'誓', '誕', '誘', '誠', '誼', '諄', '請', '諒', '諭', '諮', '諾', '謀', '謁', '謄', '謙', '謝', '謡', '謹', '譜', '譲',
'護', '豆', '豚', '豪', '貞', '貢', '貫', '貴', '賀', '賃', '賄', '賊', '賓', '賜', '賠', '賦', '購', '赦', '赳', '赴',
'趣', '距', '跳', '践', '踏', '躍', '軌', '軸', '較', '載', '輔', '輝', '輩', '轄', '辰', '辱', '迅', '迪', '迫', '迭',
'透', '逐', '逓', '逝', '逮', '逸', '遂', '遇', '遍', '遣', '遥', '遭', '遮', '遵', '遷', '遺', '遼', '避', '還', '邑',
'那', '邦', '邪', '邸', '郁', '郎', '郡', '郭', '郷', '酉', '酌', '酔', '酢', '酪', '酬', '酵', '酷', '酸', '醜', '醸',
'采', '釈', '釣', '鈴', '鉛', '鉢', '銃', '銑', '銘', '銭', '鋳', '鋼', '錘', '錠', '錦', '錬', '錯', '鍛', '鎌', '鎖',
'鎮', '鏡', '鐘', '鑑', '閑', '閣', '閥', '閲', '闘', '阻', '阿', '附', '陛', '陣', '陥', '陪', '陰', '陳', '陵', '陶',
'隆', '隊', '随', '隔', '障', '隠', '隣', '隷', '隼', '雄', '雅', '雌', '雛', '離', '雰', '雷', '需', '霊', '霜', '霞',
'霧', '露', '靖', '鞠', '韻', '響', '項', '須', '頌', '頑', '頒', '頻', '顕', '顧', '颯', '飢', '飼', '飽', '飾', '養',
'餓', '馨', '駄', '駆', '駒', '駿', '騎', '騒', '騰', '驚', '髄', '鬼', '魁', '魂', '魅', '魔', '鮎', '鮮', '鯉', '鯛',
'鯨', '鳩', '鳳', '鴻', '鵬', '鶏', '鶴', '鷹', '鹿', '麗', '麟', '麻', '麿', '黎', '黙', '黛', '鼓']

N1KANJI = ['丁', '且', '丘', '丹', '乃', '之', '乏', '乙', '也', '亀', '井', '亜', '享', '亭', '亮', '仁', '仙', '仰',
'企', '伊', '伎', '伏', '伐', '伯', '伴', '佐', '佳', '併', '価', '侮', '侵', '促', '俊', '俗', '保', '修', '俳', '俵',
'俸', '倉', '倫', '倹', '偏', '健', '偵', '偽', '傍', '傑', '傘', '催', '債', '傷', '僕', '僚', '僧', '儀', '償', '充',
'克', '免', '典', '兼', '冒', '冗', '冠', '准', '凌', '凝', '凡', '凶', '凸', '凹', '刀', '刃', '刈', '刑', '削', '剖',
'剛', '剣', '剤', '剰', '創', '功', '劣', '励', '劾', '勘', '勧', '勲', '匠', '匿', '升', '卑', '卓', '博', '即', '却',
'卸', '厄', '厳', '又', '及', '叔', '叙', '句', '司', '吉', '后', '吐', '吟', '呂', '呈', '呉', '哀', '哉', '哲', '唄',
'唆', '唇', '唯', '唱', '啓', '善', '喚', '喝', '喪', '嘆', '嘉', '嘱', '器', '噴', '囚', '圏', '坑', '坪', '垂', '垣',
'執', '培', '基', '堀', '堅', '堕', '堤', '堪', '塁', '塊', '塚', '塾', '墓', '墜', '墨', '墳', '壁', '壇', '壊', '壌',
'士', '壮', '奇', '奈', '奉', '奏', '契', '奔', '奨', '奪', '奮', '奴', '如', '妃', '妄', '妊', '妙', '妥', '妨', '姫',
'姻', '姿', '威', '娠', '娯', '婆', '婿', '媒', '媛', '嫁', '嫌', '嬉', '嬢', '孔', '孝', '孤', '宗', '宙', '宜', '宣',
'宮', '宰', '宴', '密', '寛', '寡', '寧', '審', '寮', '寸', '射', '尉', '尋', '尚', '就', '尺', '尼', '尽', '尾', '尿',
'屈', '展', '属', '履', '屯', '岐', '岡', '岬', '岳', '峠', '峡', '峰', '崇', '崎', '崩', '嵐', '巡', '巣', '巧', '己',
'帆', '帝', '帥', '帳', '幕', '幣', '幹', '幻', '幽', '庶', '康', '庸', '廃', '廉', '廊', '廷', '弁', '弊', '弓', '弔',
'弥', '弦', '弧', '張', '弾', '彩', '彫', '彰', '影', '往', '征', '径', '徐', '従', '循', '微', '徳', '徴', '徹', '忌',
'忍', '志', '応', '忠', '怠', '怪', '恒', '恨', '恩', '恭', '恵', '悔', '悟', '悠', '悦', '悼', '惑', '惜', '惨', '惰',
'愉', '愚', '慈', '態', '慎', '慕', '慢', '慨', '慮', '慰', '慶', '憂', '憤', '憧', '憩', '憲', '憶', '憾', '懇', '懐',
'懲', '懸', '我', '戒', '戯', '房', '扇', '扱', '扶', '批', '把', '抑', '抗', '択', '披', '抵', '抹', '抽', '拍', '拐',
'拒', '拓', '拘', '拙', '拠', '拡', '括', '拳', '拷', '挑', '挙', '振', '挿', '据', '授', '掌', '排', '控', '推', '掲',
'描', '提', '揚', '握', '揮', '援', '揺', '搬', '搭', '携', '搾', '摂', '摘', '摩', '撃', '撤', '撮', '撲', '擁', '擦',
'擬', '攻', '故', '敏', '救', '敢', '整', '敵', '敷', '斉', '斎', '斐', '斗', '斜', '斤', '施', '旋', '旗', '既', '旦',
'旨', '旬', '昆', '昌', '昭', '是', '晶', '智', '暁', '暇', '暑', '暖', '暦', '暫', '曙', '曹', '朗', '朱', '朴', '朽',
'杉', '杏', '条', '松', '析', '枠', '枢', '架', '柄', '某', '染', '柳', '栓', '栞', '株', '核', '栽', '桃', '案', '桑',
'桜', '桟', '梅', '梓', '梨', '棄', '棋', '棚', '棟', '椎', '検', '楓', '概', '槽', '標', '模', '樹', '欄', '欺', '款',
'歓', '殉', '殊', '殖', '殴', '殻', '氏', '汁', '江', '汰', '汽', '沖', '沙', '没', '沢', '沼', '沿', '泌', '泡', '泣',
'泰', '洞', '津', '洪', '派', '浄', '浜', '浦', '浪', '浸', '涯', '淑', '淡', '添', '渇', '渉', '渓', '渦', '湧', '源',
'溝', '滅', '滋', '滑', '滝', '滞', '漂', '漆', '漏', '漠', '漫', '漬', '漸', '潔', '潜', '潟', '潤', '潮', '澄', '激',
'濁', '瀬', '災', '炉', '炊', '炎', '為', '烈', '焦', '煩', '煮', '熊', '熟', '爽', '牧', '牲', '犠', '狂', '狙', '狩',
'独', '狭', '猛', '猟', '献', '猶', '獄', '獣', '獲', '玄', '率', '珠', '班', '琴', '瑛', '瑞', '瑠', '璃', '環', '甚',
'甲', '畔', '異', '疎', '疫', '疾', '症', '痢', '痴', '癒', '癖', '皇', '盆', '益', '盛', '盟', '監', '盤', '盲', '盾',
'眉', '看', '眺', '眼', '睡', '督', '睦', '瞬', '瞭', '瞳', '矛', '矢', '矯', '砕', '砲', '碑', '磁', '礁', '礎', '祉',
'祥', '票', '禅', '禍', '秀', '秘', '租', '秩', '称', '稚', '稲', '稼', '稿', '穀', '穂', '穏', '穫', '穴', '窃', '窒',
'窮', '竜', '端', '笛', '第', '筋', '策', '節', '範', '篤', '簿', '粋', '粗', '粘', '粛', '糖', '糧', '系', '糾', '紀',
'紋', '納', '級', '紛', '素', '紡', '索', '紫', '累', '紳', '紺', '結', '絞', '統', '絹', '継', '維', '綱', '網', '綺',
'綾', '緊', '緋', '締', '緩', '緯', '縁', '縄', '縛', '縦', '縫', '縮', '繁', '繊', '織', '繰', '罰', '罷', '羅', '羊',
'義', '翔', '翻', '翼', '耐', '聖', '聡', '聴', '肖', '肝', '肥', '肪', '肺', '胆', '胎', '胞', '胡', '胴', '脅', '脈',
'脚', '脱', '腐', '腸', '膜', '膨', '臨', '臭', '至', '致', '興', '舌', '舎', '舗', '舶', '艇', '艦', '芋', '芝', '芳',
'芽', '苗', '茂', '茎', '茜', '荘', '莉', '菊', '菌', '萌', '葬', '葵', '蒼', '蓄', '蓮', '薦', '藍', '藤', '藩', '藻',
'虎', '虐', '虚', '虜', '虹', '蚊', '蛇', '蛍', '蛮', '蝶', '融', '衆', '街', '衛', '衝', '衡', '衰', '裁', '裂', '裕',
'裸', '製', '褒', '襟', '襲', '覆', '覇', '視', '覧', '討', '託', '訟', '訳', '訴', '診', '証', '詐', '評', '詠', '詩',
'該', '詳', '誇', '誉', '誓', '誕', '誘', '誠', '請', '諒', '諭', '諮', '諾', '謙', '謝', '謡', '謹', '譜', '譲', '護',
'豆', '豚', '豪', '貞', '貢', '貫', '貴', '賀', '賃', '賄', '賊', '賓', '賠', '購', '赦', '赴', '趣', '距', '跳', '践',
'踏', '躍', '軌', '軸', '較', '載', '輔', '輝', '輩', '轄', '辱', '迅', '迫', '迭', '透', '逝', '逮', '逸', '遂', '遇',
'遍', '遣', '遥', '遭', '遮', '遷', '遺', '遼', '避', '還', '那', '邦', '邪', '邸', '郎', '郡', '郭', '郷', '酌', '酔',
'酢', '酪', '酬', '酵', '酷', '酸', '醜', '醸', '釈', '釣', '鈴', '鉛', '鉢', '銃', '銘', '銭', '鋳', '鋼', '錠', '錦',
'錬', '錯', '鍛', '鎌', '鎖', '鎮', '鏡', '鐘', '鑑', '閑', '閣', '閥', '閲', '闘', '阻', '阿', '陛', '陣', '陥', '陪',
'陰', '陳', '陵', '陶', '隆', '隊', '随', '隔', '障', '隠', '隣', '隷', '隼', '雄', '雅', '雌', '離', '雰', '雷', '需',
'霊', '霜', '霧', '露', '靖', '響', '項', '須', '頑', '頻', '顕', '顧', '颯', '飢', '飼', '飽', '飾', '養', '餓', '駄',
'駆', '駒', '駿', '騎', '騒', '騰', '驚', '髄', '鬼', '魂', '魅', '魔', '鮮', '鯉', '鯨', '鳩', '鶏', '鶴', '鹿', '麗',
'麻', '黙', '鼓']

N1KANJI_MAP = ['Street', 'Also', 'Hill', 'Rust Colored, Red', 'From', 'This', 'Scarce', 'Latter, B', 'Considerably',
'Turtle', 'Well', 'Asia', 'Receive', 'Restaurant', 'Clear', 'Humanity', 'Hermit', 'Look Up To', 'Plan', 'Italy', 'Deed',
'Bow, Lay', 'Fell, Attack', 'Chief', 'Accompany', 'Help', 'Excellent, Skilled', 'Join', 'Value', 'Despise', 'Invade',
'Urge', 'Genius', 'Vulgar', 'Preserve, Guarantee', 'Discipline', 'Haiku', 'Sack', 'Salary', 'Warehouse', 'Ethics',
'Thrifty, Frugal', 'Biased', 'Healthy', 'Spy', 'Fake', 'Nearby, Side', 'Greatness, Excellence', 'Umbrella', 'Sponsor',
'Debt', 'Wound', 'I, Me', 'Colleague', 'Priest, Monk', 'Ceremony', 'Reparation', 'Allocate', 'Overcome', 'Excuse',
'Rule', 'Concurrently', 'Dare', 'Superfluous, Unnecessary, Uselessness', 'Crown, Cap', 'Semi', 'Endure',
'Congeal, Freeze, Absorbed In', 'Mediocre', 'Villain', 'Convex, Uneven', 'Concave, Hollow', 'Sword, Katana', 'Blade',
'Prune', 'Punish', 'Whittle Down', 'Divide', 'Sturdy', 'Sword', 'Dose', 'Surplus', 'Create',
'Achievement, Accomplishment', 'Inferiority', 'Encourage', 'Censure', 'Intuition', 'Recommend', 'Merit', 'Artisan',
'Hide', 'Grid, Measure', 'Lowly, Base', 'Table', 'Exhibition, Gambling', 'Instant', 'Contrary', 'Wholesale', 'Unlucky',
'Strict', 'Again', 'Reach', 'Uncle, Aunt', 'Describe', 'Paragraph', 'Director', 'Good Luck', 'Empress',
'Throw Up, Spit, Vomit', 'Recital', 'Bath', 'Present, Display', 'Give', 'Pathetic', 'Question Mark, ?', 'Philosophy',
'Shamisen Song', 'Instigate', 'Lips', 'Solely', 'Chant', 'Enlighten', 'Morally Good, Good', 'Scream, Yell', 'Scold',
'Mourning', 'Sigh', 'Esteem, Praise', 'Request, Entrust', 'Container, Vessel', 'Erupt', 'Criminal', 'Range, Sphere',
'Pit, Hole', 'Two Mat Area', 'Dangle, Drip', 'Hedge, Fence', 'Tenacious', 'Cultivate', 'Foundation', 'Ditch', 'Solid',
'Degenerate', 'Embankment', 'Endure', 'Base, Baseball Base', 'Lump', 'Mound', 'Cram School', 'Grave', 'Crash',
'Black Ink, Ink', 'Tomb', 'Wall', 'Podium', 'Break', 'Soil, Earth', 'Samurai', 'Robust', 'Odd, Strange', 'Nara',
'Dedicate', 'Play Music', 'Pledge', 'Run, Bustle', 'Encourage', 'Rob', 'Stirred Up', 'Dude', 'Likeness',
'Princess, Queen', 'Reckless', 'Pregnant', 'Strange', 'Gentle', 'Obstruct, Impede', 'Princess', 'Marry',
'Figure, Shape, Form', 'Majesty', 'Pregnant', 'Recreation', 'Old Woman', 'Groom', 'Mediator',
'Princess, Beautiful Woman', 'Bride', 'Dislike', 'Glad, Happy', 'Miss', 'Cavity, Hole', 'Filial Piety', 'Orphan, Alone',
'Religion', 'Midair', 'Best Regards', 'Proclaim', 'Shinto Shrine, Shrine, Palace', 'Manager', 'Banquet', 'Secrecy',
'Tolerance', 'Widow', 'Rather', 'Judge', 'Dormitory', 'Measurement', 'Shoot', 'Military Officer, Military Rank',
'Inquire', 'Furthermore, Esteem', 'Settle In', 'Japanese Foot (Unit of Length)', 'Nun', 'Exhaust', 'Tail', 'Urine, Pee',
'Yield', 'Expand', 'Belong', 'Boots', 'Barracks', 'Branch Off', 'Hill', 'Cape', 'Peak', 'Ridge', 'Ravine', 'Summit',
'Worship, Revere', 'Cape', 'Crumble', 'Storm', 'Patrol', 'Nest', 'Adept', 'Oneself', 'Sail', 'Sovereign', 'Commander',
'Notebook', 'Curtain', 'Cash', 'Tree Trunk', 'Illusion', 'Secluded', 'All, Bastard', 'Ease, Peace', 'Common',
'Obsolete', 'Bargain', 'Corridor', 'Courts', 'Dialect, Speech', 'Evil', 'Bow', 'Condolence', 'Increasing',
'Chord, Bowstring', 'Arc', 'Stretch', 'Bullet', 'Coloring, Coloring', 'Carve', 'Clear, Patent', 'Shadow', 'Depart',
'Subjugate', 'Diameter', 'Gently, Gentle', 'Obey, Accompany, Follow', 'Circulation, Sequential', 'Delicate', 'Virtue',
'Indication, Sign', 'Penetrate, Clear', 'Mourning', 'Endure', 'Intention', 'Respond', 'Loyalty', 'Lazy, Neglect',
'Suspicious', 'Constant, Always', 'Grudge', 'Kindness', 'Respect', 'Favor', 'Regret', 'Comprehension', 'Leisure',
'Delight, Joy', 'Grieve, Mourn', 'Misguided', 'Frugal', 'Disaster', 'Lazy', 'Pleasant', 'Foolish', 'Mercy',
'Appearance', 'Humility', 'Yearn For, Adore', 'Ridicule, Laziness', 'Sigh', 'Consider', 'Consolation', 'Congratulate',
'Grief', 'Resent', 'Long For, Yearn', 'Rest', 'Constitution', 'Recollection', 'Remorse, Regret', 'Courteous',
'Nostalgia', 'Chastise', 'Suspend', 'I, Me', 'Commandment', 'Play', 'Cluster', 'Folding Fan', 'Handle', 'Aid',
'Criticism', 'Bundle, Grasp', 'Suppress', 'Confront', 'Select', 'Expose', 'Resist', 'Erase', 'Pluck', 'Beat', 'Kidnap',
'Refuse, Refusal', 'Cultivation', 'Arrest', 'Clumsy, Unskillful', 'Based On', 'Extend', 'Fasten', 'Fist', 'Torture',
'Challenge', 'Raise', 'Shake, Wave', 'Insert', 'Install', 'Instruct', 'Manipulate', 'Reject, Refuse', 'Abstain',
'Infer', 'Display', 'Draw', 'Present, Submit', 'Hoist', 'Grip', 'Brandish', 'Aid, Assist', 'Shake', 'Transport',
'Board, Embark', 'Portable', 'Squeeze', 'In Addition', 'Pluck', 'Chafe', 'Attack', 'Withdrawal', 'Photograph, Photo',
'Slap', 'Embrace', 'Grate', 'Imitate', 'Aggression', 'Circumstance, Reason', 'Alert', 'Rescue', 'Daring',
'Arrange, Organize', 'Enemy', 'Spread', 'Simultaneous', 'Purification', 'Patterned', 'Ladle', 'Diagonal',
'Axe, Bread Loaf Counter', 'Carry Out', 'Rotation, Revolution', 'Flag', 'Previously', 'Dawn', 'Point, Delicious',
'In Season, Time Of Month, Season', 'Descendants', 'Prosperous, Prosperity', 'Shining', 'Absolutely', 'Crystal',
'Wisdom', 'Dawn', 'Spare Time, Free Time', 'Hot, Hot Weather', 'Warm', 'Calendar', 'Temporarily', 'Dawn', 'Official',
'Bright', 'Vermillion', 'Simple, Crude', 'Rot, Decay', 'Cedar', 'Apricot', 'Clause', 'Pine, Pine Tree', 'Analysis',
'Frame', 'Hinge', 'Shelf', 'Pattern', 'Certain, One, That Person', 'Dye', 'Willow', 'Cork, Plug', 'Bookmark',
'Stocks, Shares', 'Nucleus', 'Planting', 'Peach', 'Plan', 'Mulberry', 'Sakura, Cherry Tree, Cherry Blossom',
'Jetty, Pier', 'Ume, Japanese Plum', 'Wood Block', 'Pear', 'Abandon', 'Chess Piece', 'Shelf', 'Pillar', 'Oak, Oak Tree',
'Examine', 'Maple', 'Approximation', 'Tank, Vat', 'Signpost', 'Imitation', 'Wood', 'Column, Space', 'Deceit',
'Article, Sincerity', 'Delight', 'Martyr', 'Especially', 'Multiply', 'Assault', 'Husk, Shell',
'Family Name, Last Name, Surname', 'Soup', 'Inlet, Bay', 'Select', 'Steam', 'Open Sea', 'Sand', 'Die', 'Swamp', 'Bog',
'Run Alongside', 'Secrete', 'Bubbles', 'Cry', 'Peace', 'Cave', 'Haven', 'Flood', 'Sect', 'Cleanse, Purify', 'Beach',
'Bay', 'Wander', 'Immersed', 'Horizon', 'Graceful', 'Faint', 'Append', 'Thirst', 'Ford', 'Valley', 'Whirlpool',
'Well, Boil', 'Origin', 'Gutter', 'Destroy', 'Nourishing', 'Slippery', 'Waterfall', 'Stagnate', 'Drift',
'Lacquer, Varnish', 'Leak', 'Desert, Vague', 'Manga', 'Pickle', 'Gradually, Steadily', 'Pure', 'Conceal', 'Lagoon',
'Watered', 'Tide', 'Lucidity', 'Fierce, Violent', 'Muddy, Impure', 'Rapids, Shallows', 'Disaster', 'Furnace', 'Cook',
'Flame, Blaze', 'Sake', 'Violent, Intense', 'Char', 'Annoy, Annoying', 'Boil', 'Bear', 'Ripen', 'Refreshing', 'Pasture',
'Offering', 'Sacrifice', 'Lunatic, Crazy', 'Aim', 'Hunt', 'Alone', 'Narrow', 'Fierce', 'Hunting', 'Offer', 'Still, Yet',
'Prison', 'Beast, Animal', 'Seize', 'Mysterious', 'Percent, Percentage', 'Pearl', 'Squad', 'Harp', 'Crystal',
'Congratulations', 'Lapis Lazuli', 'Glassy', 'Loop', 'Very, Great', 'Turtle Shell, A', 'Shore', 'Differ',
'Neglect, Sparse', 'Epidemic', 'Rapidly, Rapid', 'Symptom', 'Diarrhea', 'Stupid', 'Healing, Cure', 'Habit',
'Emperor', 'Lantern Festival', 'Benefit', 'Pile, Prosperous, Heap', 'Alliance', 'Oversee', 'Tray, Platter, Board',
'Blind', 'Shield', 'Eyebrows', 'Watch Over', 'Stare', 'Eyeball', 'Drowsy', 'Coach', 'Friendly', 'Blink', 'Clear',
'Pupil', 'Spear', 'Arrow', 'Correct, Straighten', 'Smash', 'Cannon', 'Tombstone', 'Magnet', 'Reef', 'Foundation',
'Welfare', 'Auspicious', 'Ballot', 'Zen, Zen Buddhism', 'Evil, Misfortune', 'Excel', 'Secret', 'Tariff',
'Order, Regularity', 'Title', 'Immature', 'Rice Plant', 'Earnings', 'Draft', 'Grain', 'Head of Plant, Ear Of Plant',
'Calm', 'Harvest', 'Hole, Cave', 'Steal', 'Suffocate', 'Destitute', 'Dragon', 'Edge', 'Flute',
'Ordinal Number Prefix, Ordinal Prefix, Number', 'Muscle, Tendon', 'Plan', 'Season', 'Example', 'Deliberate',
'Record Book', 'Stylish', 'Coarse, Rough', 'Sticky', 'Solemn', 'Sugar', 'Provisions', 'Lineage', 'Twist',
'Account, Narrative', 'Family Crest', 'Supply', 'Level, Grade, Rank', 'Distract', 'Element', 'Spinning, Spin', 'Search',
'Purple', 'Accumulate', 'Gentleman', 'Navy, Dark Blue', 'Bind, Tie', 'Strangle', 'Unite', 'Silk', 'Inherit', 'Maintain',
'Cable', 'Netting', 'Beautiful', 'Design', 'Tense', 'Scarlet', 'Tighten', 'Loose', 'Latitude', 'Edge', 'Rope',
'Bind, Restrain', 'Vertical', 'Sew', 'Shrink', 'Overgrown', 'Fiber, Slender', 'Weave', 'Spin', 'Penalty, Punishment',
'Quit, Leave', 'Spread Out, Arrange', 'Sheep', 'Righteousness', 'Fly', 'Flip', 'Wing', 'Resistant', 'Holy', 'Wise',
'Listen', 'Resemblance', 'Liver', 'Obese', 'Obese, Fat', 'Lung', 'Guts', 'Womb, Uterus', 'Cell, Placenta', 'Barbarian',
'Torso', 'Threaten', 'Vein', 'Leg', 'Undress', 'Rot', 'Intestines', 'Membrane', 'Swell', 'Look To',
'Stinking, Stinky, Smelly', 'Attain', 'Do', 'Interest', 'Tongue', 'Cottage', 'Shop, Store', 'Ship', 'Rowboat',
'Warship', 'Potato', 'Lawn', 'Perfume', 'Sprout', 'Seedling, Sapling', 'Luxuriant', 'Stem', 'Red Dye', 'Villa',
'Jasmine', 'Chrysanthemum', 'Bacteria', 'Sprout', 'Burial', 'Hollyhock', 'Pale, Blue', 'Amass', 'Lotus', 'Recommend',
'Indigo', 'Wisteria', 'Fiefdom', 'Seaweed', 'Tiger', 'Oppress', 'Void', 'Captive', 'Rainbow', 'Mosquito', 'Snake',
'Firefly', 'Barbarian', 'Butterfly', 'Dissolve', 'Populace', 'Street', 'Defense', 'Collide', 'Equilibrium', 'Decline',
'Judge', 'Split, Tear', 'Abundant, Plentiful', 'Naked, Nude', 'Manufacture', 'Praise', 'Collar', 'Attack',
'Capsize, Cover', 'Leadership', 'Look At', 'Look At', 'Chastise', 'Consign', 'Lawsuit', 'Translation, Reason', 'Sue',
'Diagnose', 'Evidence, Proof', 'Lie', 'Evaluate', 'Compose, Recite', 'Poem', 'The Above, That Specifically', 'Detailed',
'Pride', 'Honor', 'Vow', 'Birth', 'Invite', 'Sincerity', 'Request', 'Comprehend, Reality', 'Admonish', 'Consult',
'Agreement', 'Modesty', 'Apologize, Apologize', 'Noh Chanting, Noh Chant', 'Humble, Discreet', 'Genealogy, Score',
'Defer', 'Defend', 'Beans', 'Pork, Pig', 'Luxurious', 'Chastity', 'Tribute', 'Pierce, Sushi Counter', 'Valuable',
'Congratulations', 'Rent', 'Bribe', 'Robber', 'VIP, Guest', 'Compensation, Compensate', 'Subscription', 'Pardon',
'Proceed, Move On', 'Gist', 'Distance', 'Hop', 'Practice, Trample', 'Step', 'Leap', 'Rut', 'Axis', 'Contrast, Compare',
'Publish', 'Help', 'Radiance', 'Comrade', 'Control', 'Humiliate', 'Swift', 'Urge, Compel, Coerce', 'Alternate',
'Transparent', 'Die', 'Apprehend', 'Deviate, Elude', 'Accomplish', 'Treatment', 'Universal', 'Dispatch',
'Far Off, Far Away', 'Encounter, Meet', 'Intercept', 'Transition', 'Leave Behind', 'Distant', 'Dodge, Avoid',
'Send Back', 'What', 'Home Country', 'Wicked', 'Residence', 'Guy', 'County, District', 'Enclosure', 'Hometown', 'Serve',
'Drunk', 'Vinegar', 'Dairy', 'Repay', 'Fermentation, Ferment', 'Cruel, Unjust', 'Acid', 'Ugly', 'Brew', 'Explanation',
'Fishing', 'Buzzer, Small Bell', 'Lead', 'Bowl', 'Gun', 'Inscription', 'Coin', 'Cast, Casting', 'Steel', 'Lock',
'Brocade', 'Tempering', 'Confused, Mixed', 'Forge', 'Sickle, Scythe', 'Chain', 'Tranquilize', 'Mirror', 'Bell', 'Model',
'Leisure', 'The Cabinet, Cabinet', 'Clique, Clan', 'Inspection', 'Struggle', 'Thwart', 'Flatter', 'Highness',
'Army Base', 'Cave In', 'Accompany', 'Shade', 'Exhibit', 'Mausoleum, Tomb', 'Pottery', 'Prosperity', 'Squad', 'All',
'Isolate', 'Hinder', 'Hide', 'Neighbor, Neighbor', 'Slave', 'Falcon', 'Male, Brave', 'Elegant', 'Female', 'Detach',
'Atmosphere', 'Thunder', 'Demand', 'Ghost', 'Frost', 'Fog', 'Expose, Dew', 'Peaceful', 'Echo, Reverberation, Resound',
'Paragraph', 'Necessary', 'Stubborn', 'Frequent', 'Appear, Exist', 'Review', 'Quick, Sudden', 'Starve', 'Domesticate',
'Bored, Sated', 'Decorate', 'Foster', 'Starve', 'Burdensome', 'Gallop', 'Chess Piece', 'Speed', 'Horse', 'Boisterous',
'Inflation', 'Surprised', 'Marrow, Bone Marrow', 'Demon', 'Soul, Spirit', 'Alluring', 'Devil', 'Fresh', 'Carp, Koi',
'Whale', 'Dove, Pigeon', 'Chicken', 'Crane', 'Deer', 'Lovely', 'Hemp', 'Shut Up', 'Drum, Beat']

KANJI = [N5KANJI, N4KANJI, N3KANJI, N2KANJI, N1KANJI]
KANJI_MAP = [N5KANJI_MAP, N4KANJI_MAP, N3KANJI_MAP, N2KANJI_MAP, N1KANJI_MAP]

# Executes main function
if __name__ == "__main__":
    main()
