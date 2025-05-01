def calculate_cost(input_tokens, output_tokens, audioLength, char_count):
    input_cost_per_million = 0.150 #5.00 for 4o
    output_cost_per_million = 0.600 #15.00 for 4o
    
    cost = (input_tokens / 1_000_000) * input_cost_per_million + (output_tokens / 1_000_000) * output_cost_per_million
    if audioLength:
        transcription_minutes = round(audioLength / 1000 / 60)
        cost_per_minute = 0.006
        cost += cost_per_minute*transcription_minutes
        tts_cost = (char_count / 1_000_000) * output_cost_per_million
        cost += tts_cost

    return cost

# Example usage:
input_tokens = 728 + 584 + 486 + 520 + 891 + 693 # number of input tokens
output_tokens = 17 + 12  + 16 + 27 + 27 + 13# number of output tokens
audioLength = 2300 * 6
string = "It is currently 65° F and sunny in Milpitas, CA.Your Payactiv Card has a balance of $30.Your Accessible Earnings (EWA Account) has a balance of $280.Just to confirm, would you like to transfer $25 from your Accessible Earnings (EWA Account) to your Payactiv Card?$25 Successfully Transferred from Accessible Earnings to Payactiv Card 8899Your Payactiv Card currently has a balance of $55."
char_count = len(string)

cost = calculate_cost(input_tokens, output_tokens, audioLength, char_count)
print(f'Total cost: ${cost}')
print(f'Cost per 100k: ${cost*100000}')
