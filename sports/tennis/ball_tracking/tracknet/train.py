import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sports.tennis.ball_tracking.tracknet.model_pytorch import TrackNet
from sports.tennis.ball_tracking.tracknet.dataset import TrackNetDataset

# config
PRETRAINED_PATH = "sports/tennis/models/pretrained_tracknet.pt"
BATCH_SIZE = 4
LR = 1.0
EPOCHS = 50
DEVICE = "mps"

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    running_loss = 0.0

    for batch_idx, (x,y) in enumerate(loader):
        x = x.to(device)
        y = y.to(device)

        optimizer.zero_grad() # reset gradients
        out = model(x) # inference
        loss = criterion(out, y) # loss function
        print(f"train batch {batch_idx}: {loss.item():.6f}")
        loss.backward() # backprop, compute gradients
        optimizer.step() # update weights
        running_loss += loss.item()

    return running_loss / len(loader)

@torch.no_grad() # gradients are not needed for validation
def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0

    for batch_idx, (x,y) in enumerate(loader):
        x = x.to(device)
        y = y.to(device)

        out = model(x)
        loss = criterion(out, y)
        print(f"val batch {batch_idx}: {loss.item():.6f}")
        running_loss += loss.item()

    return running_loss / len(loader)

def main():
    dataset = TrackNetDataset()

    print(f"training with {len(dataset)} samples\n")

    # 90/10 val split
    val_size = int(0.1 * len(dataset))
    train_size = len(dataset) - val_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    model = TrackNet().to(DEVICE)

    # load pretrained weights
    state_dict = torch.load(PRETRAINED_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adadelta(model.parameters(), lr=LR)
 
    best_val_loss = float("inf")
 
    for epoch in range(EPOCHS):
        print(f"epoch {epoch + 1}/{EPOCHS}")
 
        train_loss = train_epoch(model, train_loader, optimizer, criterion, DEVICE)
        print("\n\n")
        val_loss = validate(model, val_loader, criterion, DEVICE)
 
        print(f"train_loss: {train_loss:.6f}  val_loss: {val_loss:.6f}")
 
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "sports/tennis/models/tracknet_ftV2.pt")
            print("\nsaved new best model\n")
 
if __name__ == "__main__":
    main()