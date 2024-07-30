# VLM-HV : Vision-Language Model Based Handwriting Verification

This repository provides implemantation of the experiments descibed in the paper VLM-HV : Vision-Language Model Based Handwriting Verification

Authors: _Mihir Chauhan, Abhishek Satbhai, Mohammad Abuzar Shaikh, Mir Basheer Ali, Bina Ramamurthy, Mingchen Gao, Siwei Lyu and Sargur Srihari_

## CEDAR Handwriting Dataset
| Dataset | Link to Drive |
|:-----------|:------------:|
| CEDAR Letter Images | [Link](https://drive.google.com/drive/folders/1fwRlwtfzV_5Pnyxm9ahQLi2eum2rDshk?usp=sharing)  |
| CEDAR AND Images| [Link](https://drive.google.com/drive/folders/1uj6eeaKBmabivxvRqrGokrcCb3B9yAHu?usp=sharing)  |

## SSL-HV Approach
<img src="vlm-hv-methods.png" height="400">

### Sequence Diagram of the code flow 

```mermaid
sequenceDiagram
    participant User
    participant Main as main()
    participant DataFrame as get_test_dataframe()
    participant ChatGPT as invoke_chatgpt()
    participant Process as process_row()
    participant Explanation as build_explanation_prompt()
    participant Resize as resize_image()
    participant Payload as build_payload()
    participant Endpoint as invoke_chatgpt_endpoint()
    participant Decision as build_decision_prompt()
    participant PostProcess as post_process_decision()
    
    User ->> Main: Start
    Main ->> DataFrame: Load DataFrame
    DataFrame ->> Main: Return DataFrame
    Main ->> ChatGPT: Invoke ChatGPT
    
    ChatGPT ->> Executor: ThreadPoolExecutor
    loop For each row
        Executor ->> Process: Process Row
        Process ->> Explanation: Build Explanation Prompt
        Explanation ->> Resize: Load and Resize Image
        Resize ->> Explanation: Return Base64 Image
        Process ->> Payload: Build Payload
        Process ->> Endpoint: Invoke ChatGPT Endpoint (Explanation)
        Endpoint ->> Process: Return Explanation Response
        
        Process ->> Decision: Build Decision Prompt
        Process ->> Payload: Build Payload
        Process ->> Endpoint: Invoke ChatGPT Endpoint (Decision)
        Endpoint ->> Process: Return Decision Response
        
        Process ->> PostProcess: Post Process Decision
        PostProcess ->> Process: Return Decision
        Process ->> Save: Save Row to Output
    end
    ChatGPT ->> Main: Return Updated DataFrame
    Main ->> User: Process Complete
```

## Cite
[VLM-HV paper]() (Accepted as short paper in [IMVIP](https://www.imvip.ie/) Proceedings Aug, 2024)
```
Upcoming
```
