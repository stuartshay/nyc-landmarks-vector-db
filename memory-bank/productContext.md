# NYC Landmarks Vector Database - Product Context

## Why This Project Exists

The NYC Landmarks Vector Database project exists to make information about New York City
landmarks more accessible and searchable. Currently, detailed information about these
landmarks exists in PDF reports stored in Azure Blob Storage, but this information is
not easily searchable or queryable. By converting these reports into vector embeddings
and storing them in a vector database, we can enable semantic search and create a
chatbot that can answer detailed questions about these landmarks.

## Problems It Solves

1. **Information Accessibility**: Detailed information about NYC landmarks is currently
   locked in PDF reports, making it difficult to access and search programmatically.
1. **Semantic Search**: Traditional text search methods cannot capture the semantic
   meaning of queries, limiting the ability to find relevant information.
1. **Information Integration**: There's a need to connect the textual information in
   PDFs with structured data in the existing Postgres database.
1. **User Engagement**: Users need an interactive way to learn about NYC landmarks
   beyond static reports.

## How It Should Work

1. **PDF Processing Pipeline**: The system should extract text from PDFs stored in Azure
   Blob Storage, process it into appropriate chunks, and generate vector embeddings
   using OpenAI's models.
1. **Vector Storage**: These embeddings should be stored in Pinecone with metadata that
   links them to the original landmarks.
1. **Query Interface**: Users should be able to query the vector database using natural
   language to find relevant information about landmarks.
1. **Chatbot Functionality**: The system should support a conversational interface that
   can answer questions about landmarks using the vector database and maintain
   conversation context.

## User Experience Goals

1. **Natural Interaction**: Users should be able to ask questions in natural language
   and receive relevant, accurate responses.
1. **Contextual Understanding**: The chatbot should maintain context across conversation
   turns, understanding follow-up questions.
1. **Specific Landmark Queries**: Users should be able to ask about specific landmarks
   by ID and receive information from that landmark's documentation.
1. **General Knowledge**: Users should be able to ask general questions about NYC
   landmarks and receive accurate information synthesized from the database.
1. **Report Generation**: The system should support generating reports about landmarks
   based on the information in the vector database.

## Target Users

1. **Researchers**: Historians, preservationists, and other researchers who need
   detailed information about NYC landmarks.
1. **Urban Planners**: Professionals who need to understand the historical and
   architectural significance of landmarks for planning purposes.
1. **Tourists and Locals**: People interested in learning about NYC landmarks for
   educational or recreational purposes.
1. **Government Officials**: City employees who need quick access to landmark
   information for official purposes.

## Success Metrics

1. **Query Accuracy**: The system should provide accurate and relevant responses to user
   queries.
1. **Response Time**: Queries should be processed and answered within a reasonable time
   frame (ideally under 2 seconds).
1. **User Satisfaction**: Users should find the system helpful and easy to use.
1. **System Scalability**: The system should be able to handle multiple concurrent users
   and scale as needed.
