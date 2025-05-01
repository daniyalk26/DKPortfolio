from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "mzbac/Phi-3-mini-4k-instruct-function-calling"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

tools = [
          {
            "type": "function",
            "function": {
                "name": "transfer_money",
                "description": "Transfer money between two accounts",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_from_id": {
                            "type": "integer",
                            "description": "The description of the account to transfer amount from must be explicitly mentioned by user",
                        },
                        "account_to_id": {
                            "type": "integer",
                            "description": "The description of the account to transfer amount to must be explicitly mentioned by user",
                        },
                        "amount": {
                            "type": "number",
                            "description": "Amount of money to transfer",
                        }
                    },
                    "required": ["account_from_id", "account_to_id", "amount"],
                },
            },
        }
    ]

messages = [
    {
        "role": "system",
        "content": "You are a helpful application chatbot with one sentence answers. Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous. Call functions as little as possible only when absolutely nesescary. Ask for user confirmation before transferring money."
    },
    {
        "role": "user",
        "content": "Use this article to help create responses: How to Transfer Your Earned Wages\r\nTo transfer your earned wages, first link your bank account or debit card to in the Payactiv app on the card page. Next, tap the blue dollar sign at the bottom of the homepage and tap “Get money”. After choosing an amount, choose your linked account, and tap \"Access my money\". It costs $3.49 to transfer your earned wages to a non-Payactiv card.\r\nTip: It's free to transfer your earned wages same-day when you set up Direct Deposit with a minimum of $200 per pay period to the Payactiv® Visa Card*.\nHow to add money to your Payactiv Visa Prepaid Card\r\nThere are five ways to load the Payactiv® Visa Card*.\r\nSet up direct paycheck deposit \r\nAccess your earned wages for free or low-cost (only offered with partnered employers).\r\nManually transfer funds from another bank account.\r\nLoad cash funds onto the card with a Moneypass ATM.\r\nLoad paper checks with Ingo Money.\r\nNote: If you received a Payactiv Prepaid Card from your HR manager, you can only load your card through paycheck Direct Deposit."
    },
    {
        "role": "user",
        "content": "{\"Current User Accounts\":[{\"id\":1,\"name\":\"Accessible Earnings\",\"balance\":0},{\"id\":2,\"name\":\"Payactiv Rewards\",\"balance\":0},{\"id\":12835,\"name\":\"Payactiv Card 8899\",\"balance\":0},{\"id\":31503,\"name\":\"Bank of America - 1111\",\"balance\":200},{\"id\":31737,\"name\":\"Chase - 1111\",\"balance\":200},{\"id\":40772,\"name\":\"Chase  - 1111\",\"balance\":200},{\"id\":44422,\"name\":\"Chase  - 0000\",\"balance\":100}]}"
    },
    {
        "role": "user",
        "content": "I want to transfer $100 from BOA to payactiv card"
    }
]

input_ids = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True, return_tensors="pt"
).to(model.device)

terminators = [tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<|end|>")]

outputs = model.generate(
    input_ids,
    max_new_tokens=256,
    eos_token_id=terminators,
    do_sample=True,
    temperature=0.1,
)
response = outputs[0]
print(tokenizer.decode(response))