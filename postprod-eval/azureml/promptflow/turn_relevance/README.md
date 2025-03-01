# Bot conversation Evaluation: Relevance

## Introduction 

The Bot Converation Relevance evaluation flow will evaluate the Query and Response for automated AI bots by leveraging the state-of-the-art Large Language Models (LLM) to measure the quality and safety of your responses. Utilizing GPT as the Language Model to assist with measurements aims to achieve a high agreement with human evaluations compared to traditional mathematical measurements.

## What you will learn

The Relevance evaluation flow allows you to assess and evaluate your model with the LLM-assisted Relevance metric.


**turn_relevance**: Measures how relevant the model's predicted answers are to the questions asked. 

Relevance metric is scored on a scale of 1 to 5, with 1 being the worst and 5 being the best. 

## Prerequisites

- Connection: Azure OpenAI.
- Data input: Evaluating the Relevance metric requires you to provide data inputs including some context, a question and an answer. 

## Tools used in this flow
- LLM tool
- Python tool