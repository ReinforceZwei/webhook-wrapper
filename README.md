# webhook-wrapper

Small application allow you to easily configure and manage multiple webhook services from web interface.

Your program will be given a unique URL for executing webhook. Later if you decided to change the webhook, just use the same unique URL. You don't even need to modify your program.

To execute the webhook, send a HTTP GET or POST request to the unique URL with parameter `content`.

## Webhook Template

Template allows you to configure the webhook request format. For example, the default template for Discord:
```json
{
    "username": "$name",
    "content": "$content"
}
```

`$name` and `$content` will be replaced when executing webhook.

You can configure your own format.