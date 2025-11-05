## Scenario

### Scenario 1

I have a paragraph of unpunctuated text in classical Chinese and I want to add punctuation and add other information to improve readability. First, the llm will punctuate the text, then it will extract all the people names, placenames, books names, and dates from the text. It will use the mcp to check the csv files from BiogRef to find out the people names, and provide the links to the databases' pages. For example, if the text contains "王安石", the llm will find the corresponding entry in the BiogRef csv file and provide a link to the CBDB page for 王安石. Similarly, for placenames, it will use the TGAZ API to find information about the places mentioned in the text. For book names, it will use the TextRef cvs files to find information about the books mentioned in the text. Finally, it will format all this information in a readable way. 


### Scenario 2

Based on scenario 1, the llm will generate annotated text in html format, with hover-over tooltips for each person name, placename, book name, and date. The tooltips will contain the information retrieved from the cbdb, dnb, kanripo, TGAZ, and other databases, including links to the relevant pages. The llm will ensure that the html is well-structured and easy to read, with appropriate use of headings, paragraphs, and other formatting elements.

### Scenario 3

It is a variant of scenario 2, but the llm will generate html format with each sentence with plain chinese, english translation, and annotations for each entity (person name, place name, book name, date) in a tabular format. Each entity will have its own row in the table, with columns for the entity type, the original text, the english translation, and the link to the relevant database page. The llm will ensure that the html is well-structured and easy to read, with appropriate use of headings, paragraphs, and other formatting elements.