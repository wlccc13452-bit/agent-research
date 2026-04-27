#!/usr/bin/env ruby

require 'pathname'

ACCENTED_MAP = {
  "a" => 'ȧ',
  "A" => 'Ȧ',
  "b" => 'ƀ',
  "B" => 'Ɓ',
  "c" => 'ƈ',
  "C" => 'Ƈ',
  "d" => 'ḓ',
  "D" => 'Ḓ',
  "e" => 'ḗ',
  "E" => 'Ḗ',
  "f" => 'ƒ',
  "F" => 'Ƒ',
  "g" => 'ɠ',
  "G" => 'Ɠ',
  "h" => 'ħ',
  "H" => 'Ħ',
  "i" => 'ī',
  "I" => 'Ī',
  "j" => 'ĵ',
  "J" => 'Ĵ',
  "k" => 'ķ',
  "K" => 'Ķ',
  "l" => 'ŀ',
  "L" => 'Ŀ',
  "m" => 'ḿ',
  "M" => 'Ḿ',
  "n" => 'ƞ',
  "N" => 'Ƞ',
  "o" => 'ǿ',
  "O" => 'Ǿ',
  "p" => 'ƥ',
  "P" => 'Ƥ',
  "q" => 'ɋ',
  "Q" => 'Ɋ',
  "r" => 'ř',
  "R" => 'Ř',
  "s" => 'ş',
  "S" => 'Ş',
  "t" => 'ŧ',
  "T" => 'Ŧ',
  "v" => 'ṽ',
  "V" => 'Ṽ',
  "u" => 'ŭ',
  "U" => 'Ŭ',
  "w" => 'ẇ',
  "W" => 'Ẇ',
  "x" => 'ẋ',
  "X" => 'Ẋ',
  "y" => 'ẏ',
  "Y" => 'Ẏ',
  "z" => 'ẑ',
  "Z" => 'Ẑ',
}
ACCENTED_MAP_Values = ACCENTED_MAP.values

SpecialVar = "\": \""

strings = ""
IO.foreach("en.js"){ |block|
    # 保留special var, 其它的字符串被替换为*
    parts = block.split(SpecialVar)
    # puts parts
    langKey = parts.at(0)
    if parts.length > 1
      langString = parts.at(1)
      langString.each_char { |c|
        if "#{ACCENTED_MAP[c]}".length >= 1
          langString.gsub!(c, "#{ACCENTED_MAP[c]}")
        end
      }
      line = langKey + SpecialVar + langString
      strings << line
    else
      strings << langKey
    end
}
puts strings
path = File.join("#{Dir.pwd}","rw.strings")
aFile = File.new(path, "r+")
if aFile
  aFile.syswrite(strings)
  puts "Success"
else
  puts "Unable to open file!"
end