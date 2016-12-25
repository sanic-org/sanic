package main

import (
	"encoding/json"
	"net/http"
	"os"
)

type TestJSONResponse struct {
	Test bool
}

func handler(w http.ResponseWriter, r *http.Request) {
	response := TestJSONResponse{true}

	js, err := json.Marshal(response)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(js)
}

func main() {
	http.HandleFunc("/", handler)
	http.ListenAndServe(":"+os.Args[1], nil)
}
